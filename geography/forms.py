from django import forms

from simulations.models import Scenario, SimulationSession

from .models import GeographyTask, MapAsset, MapProject


class MapProjectForm(forms.ModelForm):
    class Meta:
        model = MapProject
        fields = (
            'title',
            'description',
            'map_asset',
            'custom_map_image',
            'scenario',
            'task',
            'session',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['map_asset'].queryset = MapAsset.objects.filter(published=True).order_by('title')
        self.fields['map_asset'].required = False
        self.fields['custom_map_image'].required = False
        self.fields['scenario'].queryset = Scenario.objects.filter(published=True).order_by('title')
        self.fields['scenario'].required = False
        self.fields['task'].queryset = GeographyTask.objects.filter(published=True).order_by('title')
        self.fields['task'].required = False
        self.fields['session'].required = False
        if user is not None and user.is_authenticated:
            self.fields['session'].queryset = SimulationSession.objects.filter(user=user).order_by('-started_at')
        else:
            self.fields['session'].queryset = SimulationSession.objects.none()
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.FileInput):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned_data = super().clean()
        map_asset = cleaned_data.get('map_asset')
        custom_map_image = cleaned_data.get('custom_map_image')
        if map_asset and custom_map_image:
            raise forms.ValidationError('Choose either a map asset or a custom map image, not both.')
        return cleaned_data
