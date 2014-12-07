from django.db import models
from django.core.files.base import ContentFile
import datetime
import requests
import urllib2
import StringIO
import gzip


class State(models.Model):
    id = models.CharField(max_length=2,
                          primary_key=True)
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=20)
    data_file = models.FileField(upload_to='data')

    class Meta:
        ordering = ['code']

    def save_data_file(self):
        filename = 'state{}_{}.txt.gz'.format(self.id, self.code)
        url = 'http://cdiac.ornl.gov/ftp/ushcn_daily/{}'.format(filename)

        # Read the response into a StringIO buffer
        print 'Loading data: {}'.format(url)
        in_file = StringIO.StringIO()
        in_file.write(urllib2.urlopen(url).read())
        in_file.seek(0)

        # Create a new file object from the uncompresssed response
        print 'Uncompressing Gzip file: {}'.format(filename)
        out_file = gzip.GzipFile(fileobj=in_file, mode='rb')

        # Delete the exisiting file
        if self.data_file:
            print 'Deleting existing file: {}'.format(self.data_file)
            self.data_file.delete(save=False)

        # Save the new file
        print 'Saving new file: {}'.format(filename)
        self.data_file.save(filename.replace('.gz', ''), out_file)

    def import_data(self):
        if (not self.data_file):
            self.save_data_file()

        ObservationManager().import_from_file(self.data_file)

    def __str__(self):
        return self.name


class StationManager(models.Manager):
    def import_from_url(self, url):
        r = requests.get(url)
        stations = r.text

        for station in iter(stations.splitlines()):
            data = {
                'coop_id': station[0:6].strip(),
                'latitude': station[7:15].strip(),
                'longitude': station[16:25].strip(),
                'elevation': station[26:32].strip(),
                'state': State.objects.get(code=station[33:35].strip()),
                'name': station[36:66].strip(),
                'component_1': station[67:73].strip(),
                'component_2': station[74:80].strip(),
                'component_3': station[81:87].strip(),
                'utc_offset': station[88:91].strip(),
            }

            s = Station(**data)
            s.save()


class Station(models.Model):
    coop_id = models.CharField(max_length=6,
                               primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField()
    state = models.ForeignKey('State')
    name = models.CharField(max_length=30)
    component_1 = models.CharField(max_length=6)
    component_2 = models.CharField(max_length=6)
    component_3 = models.CharField(max_length=6)
    utc_offset = models.IntegerField()

    objects = StationManager()

    # def load_data(self):
        # Check if we have data for the state
        
        # If not, save the states data file

    def __str__(self):
        return self.name


class ObservationManager(models.Manager):
    def import_from_file(self, file):
        observations = file.readlines()

        for observation in observations:
            station = Station.objects.get(pk=observation[0:6].strip())
            year = int(observation[6:10].strip())
            month = int(observation[10:12].strip())
            element = observation[12:16].strip()

            for day in range(1, 32):
                try:
                    date = datetime.date(year, month, day)
                except ValueError:
                    print 'Date {}-{}-{} does not exist'.format(year, month, day)

                i = day - 1
                base = 16
                characters_per_day = 8
                start = base + (i * characters_per_day)

                data = {
                    'station': station,
                    'date': date,
                    'element': element,
                    'value': observation[start:start+5].strip(),
                    'mflag': observation[start+5].strip(),
                    'qflag': observation[start+6].strip(),
                    'sflag': observation[start+7].strip(),
                }

                print 'Saving {date}: {element}: {value}'.format(**data)
                o = Observation(**data)
                o.save()


class Observation(models.Model):
    ELEMENT_CHOICES = (
        ('PRCP', 'precipitation (hundredths of inches)'),
        ('SNOW', 'snowfall (tenths of inches)'),
        ('SNWD', 'snow depth (inches)'),
        ('TMAX', 'maximum temperature (degrees F)'),
        ('TMIN', 'minimum temperature (degrees F)'),
    )

    MFLAG_CHOICES = (
        ('', 'no measurement information applicable'),
        ('B', 'precipitation total formed from two 12-hour totals'),
        ('D', 'precipitation total formed from four six-hour totals'),
        ('H', 'represents highest or lowest hourly temperature'),
        ('K', 'converted from knots '),
        ('L', 'temperature appears to be lagged with respect to reported hour of observation '),
        ('O', 'converted from oktas '),
        ('P', 'identified as "missing presumed zero" in DSI 3200 and 3206'),
        ('T', 'trace of precipitation, snowfall, or snow depth'),
        ('W', 'converted from 16-point WBAN code (for wind direction)'),
    )

    QFLAG_CHOICES = (
        ('', 'did not fail any quality assurance check'),
        ('D', 'failed duplicate check'),
        ('G', 'failed gap check'),
        ('I', 'failed internal consistency check'),
        ('K', 'failed streak/frequent-value check'),
        ('L', 'failed check on length of multiday period '),
        ('M', 'failed megaconsistency check'),
        ('N', 'failed naught check'),
        ('O', 'failed climatological outlier check'),
        ('R', 'failed lagged range check'),
        ('S', 'failed spatial consistency check'),
        ('T', 'failed temporal consistency check'),
        ('W', 'temperature too warm for snow'),
        ('X', 'failed bounds check'),
        ('Z', 'flagged as a result of an official Datzilla investigation'),
    )

    SFLAG_CHOICES = (
        ('', 'No source (i.e., data value missing)'),
        ('0', 'U.S. Cooperative Summary of the Day (NCDC DSI-3200)'),
        ('6', 'CDMP Cooperative Summary of the Day (NCDC DSI-3206)'),
        ('7', 'U.S. Cooperative Summary of the Day -- Transmitted via WxCoder3 (NCDC DSI-3207)'),
        ('A', 'U.S. Automated Surface Observing System (ASOS) real-time data (since January 1, 2006)'),
        ('B', 'U.S. ASOS data for October 2000-December 2005 (NCDC DSI-3211)'),
        ('F', 'U.S. Fort data'),
        ('G', 'Official Global Climate Observing System (GCOS) or other government-supplied data'),
        ('H', 'High Plains Regional Climate Center real-time data'),
        ('K', 'U.S. Cooperative Summary of the Day data digitized from paper observer forms (from 2011 to present)'),
        ('M', 'Monthly METAR Extract (additional ASOS data)'),
        ('N', 'Community Collaborative Rain, Hail,and Snow (CoCoRaHS)'),
        ('R', 'NCDC Reference Network Database (Climate Reference Network and Historical Climatology Network-Modernized)'),
        ('S', 'Global Summary of the Day (NCDC DSI-9618)'),
        ('T', 'SNOwpack TELemtry (SNOTEL) data obtained from the Western Regional Climate Center'),
        ('U', 'Remote Automatic Weather Station (RAWS) data obtained from the Western Regional Climate Center'),
        ('W', 'WBAN/ASOS Summary of the Day from NCDC\'s Integrated Surface Data (ISD).'),
        ('X', 'U.S. First-Order Summary of the Day (NCDC DSI-3210)'),
        ('Z', 'Datzilla official additions or replacements'),
    )

    station = models.ForeignKey('Station',
                                db_column='coop_id')
    date = models.DateField()
    element = models.CharField(max_length=4,
                               choices=ELEMENT_CHOICES)
    value = models.IntegerField()
    mflag = models.CharField(max_length=6,
                             choices=MFLAG_CHOICES,
                             verbose_name='Measurement Flag')
    qflag = models.CharField(max_length=6,
                             choices=QFLAG_CHOICES,
                             verbose_name='Quality Flag')
    sflag = models.CharField(max_length=6,
                             choices=SFLAG_CHOICES,
                             verbose_name='Source Flag')

    objects = ObservationManager()

    def station_state(self):
        return self.station.state

    def __str__(self):
        return '{}: {}'.format(self.station.name, self.date)
