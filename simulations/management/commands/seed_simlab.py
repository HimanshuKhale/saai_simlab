from django.core.management.base import BaseCommand

from simulations.models import Role, Scenario, SimulationType


SIMULATION_TYPES = [
    {
        'name': 'Geography Map Lab',
        'slug': 'geography-map-lab',
        'description': 'Map-based investigations for physical features, cities, rivers, routes, and spatial reasoning.',
        'icon': 'Map',
        'order': 1,
        'configuration': {'category': 'geography', 'supports_map_assets': True},
    },
    {
        'name': 'Civics Parliament Lab',
        'slug': 'civics-parliament-lab',
        'description': 'Role-play parliamentary procedure, accountability, motions, debate, and constitutional choices.',
        'icon': 'Civics',
        'order': 2,
        'configuration': {'category': 'civics', 'supports_turns': True},
    },
    {
        'name': 'History Character Debate',
        'slug': 'history-character-debate',
        'description': 'Historically grounded character debates with journals, trade-offs, and contextual decisions.',
        'icon': 'History',
        'order': 3,
        'configuration': {'category': 'history', 'supports_character_profiles': True},
    },
    {
        'name': 'Business Negotiation Lab',
        'slug': 'business-negotiation-lab',
        'description': 'Negotiation practice with roles, constraints, business documents, and measurable outcomes.',
        'icon': 'Business',
        'order': 4,
        'configuration': {'category': 'business', 'supports_documents': True},
    },
]


SCENARIOS = [
    {
        'type_slug': 'geography-map-lab',
        'title': 'India Physical Features Marking',
        'slug': 'india-physical-features-marking',
        'summary': 'Mark major physical divisions of India and justify spatial relationships.',
        'description': 'Students identify the Himalayas, northern plains, plateau regions, coastal plains, deserts, and islands on a working map.',
        'difficulty': 'Foundation',
        'estimated_minutes': 40,
        'objectives': ['Identify major physical divisions', 'Explain how terrain shapes settlement and routes'],
        'variables': {'map_scope': 'india', 'features_required': 12},
        'roles': ['Cartographer', 'Geography Reviewer'],
    },
    {
        'type_slug': 'geography-map-lab',
        'title': 'Madhya Pradesh Cities, Rivers and Railways',
        'slug': 'madhya-pradesh-cities-rivers-and-railways',
        'summary': 'Map important cities, rivers, and railway links across Madhya Pradesh.',
        'description': 'Students connect urban centers, river systems, and transport corridors to understand regional geography.',
        'difficulty': 'Intermediate',
        'estimated_minutes': 45,
        'objectives': ['Locate key cities and rivers', 'Trace railway connectivity', 'Infer regional economic links'],
        'variables': {'map_scope': 'madhya_pradesh', 'layers': ['cities', 'rivers', 'railways']},
        'roles': ['Regional Planner', 'Map Auditor'],
    },
    {
        'type_slug': 'civics-parliament-lab',
        'title': 'Water Crisis and Ministerial Accountability',
        'slug': 'water-crisis-and-ministerial-accountability',
        'summary': 'Debate responsibility and procedure during a public water crisis.',
        'description': 'Participants use questions, statements, and accountability motions to examine executive responsibility.',
        'difficulty': 'Intermediate',
        'estimated_minutes': 50,
        'objectives': ['Practice parliamentary questioning', 'Separate policy failure from administrative failure'],
        'variables': {'issue': 'water_crisis', 'available_motions': ['question_hour', 'calling_attention', 'censure']},
        'roles': ['Water Resources Minister', 'Opposition MLA', 'Speaker'],
    },
    {
        'type_slug': 'civics-parliament-lab',
        'title': 'Anti-Defection and Party Whip',
        'slug': 'anti-defection-and-party-whip',
        'summary': 'Examine party discipline, voting, and disqualification in a legislature.',
        'description': 'Participants test constitutional reasoning around the party whip and anti-defection rules.',
        'difficulty': 'Advanced',
        'estimated_minutes': 55,
        'objectives': ['Apply anti-defection principles', 'Argue competing democratic values'],
        'variables': {'constitutional_topic': 'anti_defection', 'vote_margin': 'narrow'},
        'roles': ['Party Whip', 'Dissenting Member', 'Speaker'],
    },
    {
        'type_slug': 'history-character-debate',
        'title': 'Bengal 1937: Trade, Power and Survival',
        'slug': 'bengal-1937-trade-power-and-survival',
        'summary': 'Negotiate political and economic choices in Bengal during a turbulent period.',
        'description': 'Students inhabit historical perspectives and debate trade, governance, and survival under pressure.',
        'difficulty': 'Advanced',
        'estimated_minutes': 60,
        'objectives': ['Use historical context in debate', 'Track consequences of decisions over time'],
        'variables': {'year': 1937, 'region': 'bengal', 'pressure_points': ['trade', 'coalitions', 'food_security']},
        'roles': ['Provincial Leader', 'Trader', 'Community Organizer'],
    },
    {
        'type_slug': 'business-negotiation-lab',
        'title': 'First Export Order Negotiation',
        'slug': 'first-export-order-negotiation',
        'summary': 'Negotiate pricing, delivery, quality terms, and payment for a first export order.',
        'description': 'Learners prepare offers, respond to constraints, and produce practical negotiation documents.',
        'difficulty': 'Foundation',
        'estimated_minutes': 50,
        'objectives': ['Negotiate commercial terms', 'Balance risk, price, and trust', 'Draft a basic order summary'],
        'variables': {'currency': 'USD', 'buyer_priority': 'reliability', 'seller_priority': 'advance_payment'},
        'roles': ['Exporter', 'Overseas Buyer', 'Logistics Advisor'],
    },
]


class Command(BaseCommand):
    help = 'Seed SAAI SimLab with foundation simulation types and sample scenarios.'

    def handle(self, *args, **options):
        type_lookup = {}
        for item in SIMULATION_TYPES:
            simulation_type, _ = SimulationType.objects.update_or_create(
                slug=item['slug'],
                defaults={**item, 'published': True},
            )
            type_lookup[item['slug']] = simulation_type

        for item in SCENARIOS:
            roles = item['roles']
            simulation_type = type_lookup[item['type_slug']]
            scenario_defaults = {
                key: value
                for key, value in item.items()
                if key not in {'roles', 'type_slug', 'slug'}
            }
            scenario, _ = Scenario.objects.update_or_create(
                simulation_type=simulation_type,
                slug=item['slug'],
                defaults={**scenario_defaults, 'simulation_type': simulation_type, 'published': True},
            )
            for role_name in roles:
                Role.objects.update_or_create(
                    scenario=scenario,
                    slug=role_name.lower().replace(' ', '-'),
                    defaults={
                        'name': role_name,
                        'description': f'{role_name} role for {scenario.title}.',
                        'objectives': scenario.objectives,
                        'initial_state': {'ready': True},
                    },
                )

        self.stdout.write(self.style.SUCCESS('Seeded SAAI SimLab foundation data.'))
