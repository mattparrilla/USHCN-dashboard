from django.contrib import admin
from data.models import State, Station, Observation


class StateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'data_file')
    search_fields = ['name']
    actions = ['save_data_file', 'import_data']
    list_per_page = 100

    def save_data_file(self, request, queryset):
        for state in queryset:
            state.save_data_file()
    save_data_file.short_description = "Save data file for selected states"


    def import_data(self, request, queryset):
        for state in queryset:
            state.import_data()
    import_data.short_description = "Import data to database for selected states"

admin.site.register(State, StateAdmin)


class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'elevation')
    list_filter = ['state']
    search_fields = ['name']
    list_per_page = 100

admin.site.register(Station, StationAdmin)


class ObservationAdmin(admin.ModelAdmin): 
    list_display = ('station', 'station_state', 'date', 'element', 'value')
    list_filter = ['station', 'element']
    list_per_page = 100

admin.site.register(Observation, ObservationAdmin)
