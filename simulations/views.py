from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Role, Scenario, SimulationEvent, SimulationSession, SimulationType


def dashboard(request):
    simulation_types = SimulationType.objects.filter(published=True).order_by('order', 'name')
    return render(request, 'simulations/dashboard.html', {'simulation_types': simulation_types})


def scenario_list(request, simulation_type_slug):
    simulation_type = get_object_or_404(
        SimulationType,
        slug=simulation_type_slug,
        published=True,
    )
    scenarios = simulation_type.scenarios.filter(published=True).order_by('title')
    return render(
        request,
        'simulations/scenario_list.html',
        {'simulation_type': simulation_type, 'scenarios': scenarios},
    )


def scenario_detail(request, simulation_type_slug, scenario_slug):
    scenario = get_object_or_404(
        Scenario.objects.select_related('simulation_type').prefetch_related('roles', 'characters'),
        simulation_type__slug=simulation_type_slug,
        slug=scenario_slug,
        published=True,
        simulation_type__published=True,
    )
    return render(request, 'simulations/scenario_detail.html', {'scenario': scenario})


@login_required
@require_POST
def start_session(request, scenario_id):
    scenario = get_object_or_404(Scenario, pk=scenario_id, published=True)
    role = None
    role_id = request.POST.get('role')
    if role_id:
        role = get_object_or_404(Role, pk=role_id, scenario=scenario)

    current_state = {
        'scenario_variables': scenario.variables,
        'role_state': role.initial_state if role else {},
        'status': 'started',
    }
    session = SimulationSession.objects.create(
        scenario=scenario,
        simulation_type=scenario.simulation_type,
        user=request.user,
        selected_role=role,
        current_state=current_state,
    )
    SimulationEvent.objects.create(
        session=session,
        sequence=1,
        event_type='session_started',
        actor_role=role,
        message='Simulation session started.',
        payload={'role': role.slug if role else None},
    )
    return redirect(session)


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(
        SimulationSession.objects.select_related(
            'scenario',
            'simulation_type',
            'selected_role',
            'user',
        ).prefetch_related('events'),
        pk=session_id,
    )
    if session.user != request.user and not request.user.is_staff:
        raise PermissionDenied
    return render(request, 'simulations/session_detail.html', {'session': session})

# Create your views here.
