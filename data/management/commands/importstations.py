from django.core.management.base import BaseCommand, CommandError
from data.models import StationManager

class Command(BaseCommand):
    help = 'Imports the station data from USHCN FTP Directory'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        StationManager().import_from_url('http://cdiac.ornl.gov/ftp/ushcn_daily/ushcn-stations.txt')
        self.stdout.write('Successfully imported stations')
