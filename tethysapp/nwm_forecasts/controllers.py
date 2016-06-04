from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render_to_response
from tethys_sdk.gizmos import SelectInput, ToggleSwitch, Button
from django.conf import settings
from hs_restclient import HydroShare, HydroShareAuthOAuth2

import os
import netCDF4 as nc
import json
import datetime as dt
import numpy as np
import shapefile
import tempfile

hs_hostname = 'www.hydroshare.org'


@login_required()
def home(request):
    """
    Controller for the app home page.
    """

    config_input = SelectInput(display_text='Enter Configuration',
                               name='config',
                               multiple=False,
                               options=[('Analysis and Assimilation', 'analysis_assim'),
                                        ('Short Range', 'short_range'),
                                        ('Medium Range', 'medium_range'),
                                        ('Long Range', 'long_range')],
                               initial=['Short Range'],
                               original=True)

    geom_input = SelectInput(display_text='Enter Geometry',
                             name='geom',
                             multiple=False,
                             options=[('Channel', 'channel_rt'),
                                      ('Land', 'land'),
                                      ('Reservoir', 'reservoir')],
                             initial=['Channel'],
                             original=True)

    start_date = {
        'display_text': 'Enter Beginning Date',
        'name': 'startDate',
        'end_date': '0d',
        'autoclose': True,
        'format': 'yyyy-mm-dd',
        'start_date': '2016-05-01',
        'today_button': True,
        'initial': dt.datetime.utcnow().strftime("%Y-%m-%d")
    }

    end_date = {
        'name': 'endDate',
        'end_date': '0d',
        'autoclose': True,
        'format': 'yyyy-mm-dd',
        'start_date': '2016-05-01',
        'today_button': True,
        'classes': 'hidden',
        'initial': dt.datetime.utcnow().strftime("%Y-%m-%d")
    }

    start_time = SelectInput(display_text='Enter Beginning Time',
                             name='time',
                             multiple=False,
                             options=[('12:00 am', '00'), ('01:00 am', '01'),
                                      ('02:00 am', '02'), ('03:00 am', '03'),
                                      ('04:00 am', '04'), ('05:00 am', '05'),
                                      ('06:00 am', '06'), ('07:00 am', '07'),
                                      ('08:00 am', '08'), ('09:00 am', '09'),
                                      ('10:00 am', '10'), ('11:00 am', '11'),
                                      ('12:00 pm', '12'), ('01:00 pm', '13'),
                                      ('02:00 pm', '14'), ('03:00 pm', '15'),
                                      ('04:00 pm', '16'), ('05:00 pm', '17'),
                                      ('06:00 pm', '18'), ('07:00 pm', '19'),
                                      ('08:00 pm', '20'), ('09:00 pm', '21'),
                                      ('10:00 pm', '22'), ('11:00 pm', '23')],
                             initial=['12:00 am'],
                             original=True)

    longRangeLag00 = ToggleSwitch(display_text='', name='00z', size='mini', initial=True)
    longRangeLag06 = ToggleSwitch(display_text='', name='06z', size='mini')
    longRangeLag12 = ToggleSwitch(display_text='', name='12z', size='mini')
    longRangeLag18 = ToggleSwitch(display_text='', name='18z', size='mini')

    submit_button = Button(display_text='Submit',
                           name='submit',
                           attributes='id="submitBtn" form=paramForm value="Success"',
                           submit=True)

    if request.GET:
        # Make the waterml url query string
        config = request.GET['config']
        geom = request.GET['geom']
        if geom != 'land':
            comid = request.GET['COMID']
        else:
            comid = ','.join([request.GET['Y'], request.GET['X']])
        lon = request.GET['longitude']
        lat = request.GET['latitude']
        startDate = request.GET['startDate']
        endDate = request.GET['endDate']
        time = request.GET['time']

        watershed_obj = None
        if request.GET.get('watershed'):
            watershed = request.GET['watershed']
            args = watershed.split(':')
            watershed_obj = get_geojson_from_hs_resource(args[0], args[1], request)

        lagList = []
        if '00z' in request.GET:
            lagList.append('t00z')
        if '06z' in request.GET:
            lagList.append('t06z')
        if '12z' in request.GET:
            lagList.append('t12z')
        if'18z' in request.GET:
            lagList.append('t18z')

        lag = ','.join(lagList)
        # time2 = '00:00:00'
        waterml_url = '?config=%s&COMID=%s&lon=%s&lat=%s&date=%s&time=%s&lag=%s' % (config, comid, lon, lat, startDate,
                                                                                    time, lag)

        # waterML_button = Button(display_text='Get WaterML',
        #                    name='waterMLBtn',
        #                    attributes='target="_blank" href="/apps/nwm-forecasts/waterml{{waterml_url}}',
        #                    submit=False)

        # HS_button = Button(display_text='Add to HydroShare',
        #                    name='HSBtn',
        #                    attributes='id="HSBtn" data-toggle="modal" data-target="#hydroshare-modal"',
        #                    submit=False)

        # HSGIS_button = Button(display_text='Add to HydroShare GIS',
        #                       name='HSGISBtn',
        #                       attributes='',
        #                       submit=False)

        context = {
            'config_input': config_input,
            'geom_input': geom_input,
            'start_date': start_date,
            'end_date': end_date,
            'start_time': start_time,
            # 'end_date': end_date,
            'longRangeLag00': longRangeLag00,
            'longRangeLag06': longRangeLag06,
            'longRangeLag12': longRangeLag12,
            'longRangeLag18': longRangeLag18,
            'submit_button': submit_button,
            # 'waterML_button': waterML_button,
            # 'HS_button': HS_button,
            # 'HSGIS_button': HSGIS_button,
            'waterml_url': waterml_url,
            'watershed': watershed_obj
        }

        return render(request, 'nwm_forecasts/home.html', context)

    else:
        context = {
            'config_input': config_input,
            'geom_input': geom_input,
            'start_date': start_date,
            'start_time': start_time,
            'end_date': end_date,
            'longRangeLag00': longRangeLag00,
            'longRangeLag06': longRangeLag06,
            'longRangeLag12': longRangeLag12,
            'longRangeLag18': longRangeLag18,
            'submit_button': submit_button
        }
        return render(request, 'nwm_forecasts/home.html', context)


def get_netcdf_data(request):
    if request.method == 'GET':
        get_data = request.GET
        ts_pairs_data = {}  # For time series pairs data

        try:
            config = get_data['config']
            geom = get_data['geom']
            if geom != 'land':
                comid = int(get_data['comid'])
            else:
                comid = get_data['comid']
            startDate = get_data['startDate']
            time = get_data['time']
            lag = get_data['lag'].split(',')

            if config == 'short_range' or config == 'medium_range':

                timeCheck = ''.join(['t', time, 'z'])

                app_dir = '/projects/water/nwm/data/'
                dateDir = startDate.replace('-', '')
                localFileDir = os.path.join(app_dir, config, dateDir)
                nc_files = sorted([x for x in os.listdir(localFileDir) if geom in x and timeCheck in x and 'georeferenced' in x])

                local_file_path = os.path.join(localFileDir, nc_files[0])
                prediction_data = nc.Dataset(local_file_path, mode="r")

                if geom == 'channel_rt':
                    comidList = prediction_data.variables['station_id'][:]
                    comidIndex = int(np.where(comidList == comid)[0])
                    var = 'streamflow'
                elif geom == 'reservoir':
                    comidList = prediction_data.variables['lake_id'][:]
                    comidIndex = int(np.where(comidList == comid)[0])
                    var = 'inflow'
                elif geom == 'land':
                    comidList = comid.split(',')
                    comidIndexY = int(comidList[0])
                    comidIndexX = int(comidList[1])
                    var = 'ACCET'
                else:
                    return JsonResponse({'error': "Invalid netCDF file"})

                variables = prediction_data.variables.keys()
                if 'time' in variables:
                    time = [int(nc.num2date(0, prediction_data.variables['time'].units).strftime('%s'))]
                else:
                    return JsonResponse({'error': "Invalid netCDF file"})

                q_out = []
                for ncf in nc_files:
                    local_file_path = os.path.join(localFileDir, ncf)
                    prediction_dataTemp = nc.Dataset(local_file_path, mode="r")

                    if geom != 'land':
                        q_outT = prediction_dataTemp.variables[var][comidIndex].tolist()
                        q_out.append(round(q_outT * 35.3147, 4))
                    else:
                        q_outT = prediction_dataTemp.variables[var][0][comidIndexY][comidIndexX].tolist()
                        q_out.append(round(q_outT * 0.0393701, 4))

                ts_pairs_data[str(comid)] = [time, q_out, 'notLong']

                return JsonResponse({
                    "success": "Data analysis complete!",
                    "ts_pairs_data": json.dumps(ts_pairs_data)
                })

            elif config == 'analysis_assim':

                endDate = get_data['endDate'].replace('-', '')

                app_dir = '/projects/water/nwm/data/'
                dateDir = startDate.replace('-', '')
                localFileDir = os.path.join(app_dir, config)
                nc_files = sorted([x for x in os.listdir(localFileDir) if 'channel_rt' in x and
                                   int(x.split('.')[1]) >= int(dateDir) and int(x.split('.')[1]) < int(endDate) and
                                   'georeferenced' in x])


                local_file_path = os.path.join(localFileDir, nc_files[0])
                prediction_data = nc.Dataset(local_file_path, mode="r")

                qout_dimensions = prediction_data.variables['station_id'].dimensions

                if qout_dimensions[0] == 'station':
                    comidList = prediction_data.variables['station_id'][:]
                    comidIndex = int(np.where(comidList == comid)[0])
                else:
                    return JsonResponse({'error': "Invalid netCDF file"})

                variables = prediction_data.variables.keys()
                if 'time' in variables:
                    time = [int(nc.num2date(0, prediction_data.variables['time'].units).strftime('%s'))]
                else:
                    return JsonResponse({'error': "Invalid netCDF file"})

                q_out = []
                for ncf in nc_files:
                    local_file_path = os.path.join(localFileDir, ncf)
                    prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
                    q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
                    q_out.append(round(q_outT * 35.3147, 4))

                ts_pairs_data[str(comid)] = [time, q_out, 'notLong']

                return JsonResponse({
                    "success": "Data analysis complete!",
                    "ts_pairs_data": json.dumps(ts_pairs_data)
                })

            elif config == 'long_range':
                q_out_group = []
                for lg in lag:
                    timeCheck = ''.join(['t', lg])

                    app_dir = '/projects/water/nwm/data/'
                    dateDir = startDate.replace('-', '')
                    localFileDir = os.path.join(app_dir, config, dateDir)
                    nc_files_1 = sorted([x for x in os.listdir(localFileDir) if
                                         'channel_rt_1' in x and timeCheck in x and 'georeferenced' in x])
                    nc_files_2 = sorted([x for x in os.listdir(localFileDir) if
                                         'channel_rt_2' in x and timeCheck in x and 'georeferenced' in x])
                    nc_files_3 = sorted([x for x in os.listdir(localFileDir) if
                                         'channel_rt_3' in x and timeCheck in x and 'georeferenced' in x])
                    nc_files_4 = sorted([x for x in os.listdir(localFileDir) if
                                         'channel_rt_4' in x and timeCheck in x and 'georeferenced' in x])

                    local_file_path = os.path.join(localFileDir, nc_files_1[0])
                    prediction_data = nc.Dataset(local_file_path, mode="r")

                    qout_dimensions = prediction_data.variables['station_id'].dimensions

                    if qout_dimensions[0] == 'station':
                        comidList = prediction_data.variables['station_id'][:]
                        comidIndex = int(np.where(comidList == comid)[0])
                    else:
                        return JsonResponse({'error': "Invalid netCDF file"})

                    variables = prediction_data.variables.keys()
                    if 'time' in variables:
                        time = [int(nc.num2date(0, prediction_data.variables['time'].units).strftime('%s'))]
                    else:
                        return JsonResponse({'error': "Invalid netCDF file"})

                    q_out_1 = []
                    for ncf in nc_files_1:
                        local_file_path = os.path.join(localFileDir, ncf)
                        prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
                        q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
                        q_out_1.append(round(q_outT * 35.3147, 4))
                    q_out_2 = []
                    for ncf in nc_files_2:
                        local_file_path = os.path.join(localFileDir, ncf)
                        prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
                        q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
                        q_out_2.append(round(q_outT * 35.3147, 4))
                    q_out_3 = []
                    for ncf in nc_files_3:
                        local_file_path = os.path.join(localFileDir, ncf)
                        prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
                        q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
                        q_out_3.append(round(q_outT * 35.3147, 4))
                    q_out_4 = []
                    for ncf in nc_files_4:
                        local_file_path = os.path.join(localFileDir, ncf)
                        prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
                        q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
                        q_out_4.append(round(q_outT * 35.3147, 4))

                    q_out_group.append([time, q_out_1, q_out_2, q_out_3, q_out_4, timeCheck])

                ts_pairs_data[str(comid)] = q_out_group

                return JsonResponse({
                    "success": "Data analysis complete!",
                    "ts_pairs_data": json.dumps(ts_pairs_data)
                })

        except Exception as e:
            print str(e)
            return JsonResponse({'error': 'No data found for the selected reach.'})
    else:
        return JsonResponse({'error': "Bad request. Must be a GET request."})


# ***----------------------------------------------------------------------------------------*** #
# ***                                                                                        *** #
# ***                                     REST API                                           *** #
# ***                                                                                        *** #
# ***----------------------------------------------------------------------------------------*** #

def getTimeSeries(comid, date, time, config, lag=''):
    if config != 'long_range':
        timeCheck = ''.join(['t', time, 'z'])

        ts = []

        app_dir = '/projects/water/nwm/data/'
        dateDir = date.replace('-', '')
        localFileDir = os.path.join(app_dir, config, dateDir)
        nc_files = sorted([x for x in os.listdir(localFileDir) if
                           'channel_rt' in x and timeCheck in x and 'georeferenced' in x])
        ncFile = nc.Dataset(os.path.join(localFileDir, nc_files[0]), mode="r")
        comidList = ncFile.variables['station_id'][:]
        comidIndex = int(np.where(comidList == int(comid))[0])

        for ncf in nc_files:
            local_file_path = os.path.join(localFileDir, ncf)
            prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
            q_out = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
            ts.append(round(q_out * 35.3147, 4))
        return ts
    elif config == 'long_range':
        ts_group = []
        app_dir = '/projects/water/nwm/data/'
        dateDir = startDate.replace('-', '')
        localFileDir = os.path.join(app_dir, config, dateDir)
        nc_files_1 = sorted([x for x in os.listdir(localFileDir) if
                             'channel_rt_1' in x and lag in x and 'georeferenced' in x])
        nc_files_2 = sorted([x for x in os.listdir(localFileDir) if
                             'channel_rt_2' in x and lag in x and 'georeferenced' in x])
        nc_files_3 = sorted([x for x in os.listdir(localFileDir) if
                             'channel_rt_3' in x and lag in x and 'georeferenced' in x])
        nc_files_4 = sorted([x for x in os.listdir(localFileDir) if
                             'channel_rt_4' in x and lag in x and 'georeferenced' in x])

        prediction_data = nc.Dataset(os.path.join(localFileDir, nc_files_1[0]), mode="r")
        comidList = prediction_data.variables['station_id'][:]
        comidIndex = int(np.where(comidList == comid)[0])

        time = [int(nc.num2date(0, prediction_data.variables['time'].units).strftime('%s'))]

        q_out_1 = []
        for ncf in nc_files_1:
            local_file_path = os.path.join(localFileDir, ncf)
            prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
            q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
            q_out_1.append(round(q_outT * 35.3147, 4))
        q_out_2 = []
        for ncf in nc_files_2:
            local_file_path = os.path.join(localFileDir, ncf)
            prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
            q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
            q_out_2.append(round(q_outT * 35.3147, 4))
        q_out_3 = []
        for ncf in nc_files_3:
            local_file_path = os.path.join(localFileDir, ncf)
            prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
            q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
            q_out_3.append(round(q_outT * 35.3147, 4))
        q_out_4 = []
        for ncf in nc_files_4:
            local_file_path = os.path.join(localFileDir, ncf)
            prediction_dataTemp = nc.Dataset(local_file_path, mode="r")
            q_outT = prediction_dataTemp.variables['streamflow'][comidIndex].tolist()
            q_out_4.append(round(q_outT * 35.3147, 4))

        ts_group.append([q_out_1, q_out_2, q_out_3, q_out_4, time])
        return ts_group


def format_time_series(config, startDate, ts, time, nodata_value):
    nDays = len(ts)
    if config == 'short_range' or config == 'analysis_assim':
        datelist = [dt.datetime.strptime(startDate, "%Y-%m-%d") + dt.timedelta(hours=x + int(time) +1) for x in range(0,nDays)]
    elif config == 'medium_range':
        datelist = [dt.datetime.strptime(startDate, "%Y-%m-%d") + dt.timedelta(hours=x+9) for x in range(0, nDays*3, 3)]
    formatted_ts = []
    for i in range(0, nDays):
        formatted_val = ts[i]
        if (formatted_val is None):
            formatted_val = nodata_value
        formatted_date = datelist[i].strftime('%Y-%m-%dT%H:%M:%S')
        formatted_ts.append({'date':formatted_date, 'val':formatted_val})

    print len(ts), formatted_ts, '********************'
    return formatted_ts


def get_site_name(lat, lon):
    lat_name = "Lat: %s" % lat
    lon_name = "Lon: %s" % lon
    return lat_name + ' ' +  lon_name


def get_data_waterml(request):
    """
	Controller that will show the data in WaterML 1.1 format
	"""
    if request.GET:
        config = request.GET["config"]
        comid = request.GET["COMID"]
        lat = request.GET["lat"]
        lon = request.GET["lon"]
        start = request.GET["date"]
        time = request.GET['time']
        # lagList = request.GET['lag'].split(',')

        nodata_value = -9999
        if config != 'long_range':
            ts = getTimeSeries(comid, start, time, config)
            time_series = format_time_series(config, start, ts, time, nodata_value)
            site_name = get_site_name(float(lat), float(lon))
            context = {
                'config': config,
                'comid': comid,
                'lat': lat,
                'lon': lon,
                'startdate': start,
                'site_name': site_name,
                'time_series': time_series
            }

            xmlResponse = render_to_response('nwm_forecasts/waterml.xml', context)
            xmlResponse['Content-Type'] = 'application/xml'
            xmlResponse['content-disposition'] = "attachment; filename=output-time-series.xml"
            return xmlResponse
        elif config == 'long_range':
            # for lg in lagList:
            #     ts_group = getTimeSeries(comid, start, time, config, lg)
            #     ts_group_formatted = []
            #     for ts in ts_group[0:-1]:
            #         ts_group_formatted.append(format_time_series(config, ts_group[-1], ts, nodata_value))
            #     site_name = lg + ' ' + get_site_name(float(lat), float(lon))
            #     for ts_f in ts_group_formatted:
            #         context = {
            #             'config': config,
            #             'comid': comid,
            #             'lat': lat,
            #             'lon': lon,
            #             'startdate': start,
            #             'site_name': site_name,
            #             'time_series': ts_f
            #         }
            #
            #         xmlResponse = render_to_response('nwm_forecasts/waterml.xml', context)
            # xmlResponse['Content-Type'] = 'application/xml'
            # xmlResponse['content-disposition'] = "attachment; filename=output-time-series.xml"
            # return xmlResponse
            raise Http404('A zip file download for all long range forecasts is in development.')


def get_hs_watershed_list(request):
    response_obj = {}
    if request.is_ajax() and request.method == 'GET':
        resources_list = []
        hs = get_hs_object(request)
        if hs is None:
            response_obj['error'] = 'You must be signed in through HydroShare to access this feature. ' \
                                    'Please log out and then sign in again using your HydroShare account.'
        else:
            creator = None
            try:
                creator = hs.getUserInfo()['username']
            except Exception:
                pass

            valid_res_types = ['GenericResource', 'GeographicFeatureResource']
            valid_file_extensions = ['.shp', '.geojson']

            for resource in hs.getResourceList(types=valid_res_types, creator=creator):
                res_id = resource['resource_id']
                try:
                    for res_file in hs.getResourceFileList(res_id):
                        filename = os.path.basename(res_file['url'])
                        if os.path.splitext(filename)[1] in valid_file_extensions:
                            resources_list.append({
                                'title': resource['resource_title'],
                                'id': res_id,
                                'owner': resource['creator'],
                                'filename': filename
                            })
                            break
                except Exception as e:
                    print str(e)
                    continue

            resources_json = json.dumps(resources_list)

            response_obj['success'] = 'Resources obtained successfully.'
            response_obj['resources'] = resources_json

        return JsonResponse(response_obj)


def get_hs_object(request):
    try:
        hs = get_oauth_hs(request)
    except Exception as e:
        print str(e)
        hs = None
    return hs


def get_oauth_hs(request):
    global hs_hostname

    client_id = getattr(settings, 'SOCIAL_AUTH_HYDROSHARE_KEY', 'None')
    client_secret = getattr(settings, 'SOCIAL_AUTH_HYDROSHARE_SECRET', 'None')

    # Throws django.core.exceptions.ObjectDoesNotExist if current user is not signed in via HydroShare OAuth
    token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']
    auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)

    return HydroShare(auth=auth, hostname=hs_hostname, use_https=True)


def load_watershed(request):
    geojson_str = None

    if request.is_ajax() and request.method == 'GET':
        res_id = str(request.GET['res_id'])
        filename = str(request.GET['filename'])
        response_obj = get_geojson_from_hs_resource(res_id, filename, request)
        return JsonResponse(response_obj)


def get_geojson_from_hs_resource(res_id, filename, request):
    response_obj = {}
    try:
        hs = get_hs_object(request)

        if filename.endswith('.geojson'):
            geojson_str = str(hs.getResourceFile(pid=res_id, filename=filename).next())

            response_obj['type'] = 'geojson'

        elif filename.endswith('.shp'):
            proj_str = str(hs.getResourceFile(pid=res_id, filename=filename.replace('.shp', '.prj')).next())
            '''
            Credit: The following code was adapted from https://gist.github.com/frankrowe/6071443
            '''
            # Read the shapefile-like object
            with tempfile.TemporaryFile() as f1:
                for chunk in hs.getResourceFile(pid=res_id, filename=filename):
                    f1.write(chunk)
                with tempfile.TemporaryFile() as f2:
                    for chunk in hs.getResourceFile(pid=res_id, filename=filename.replace('.shp', '.dbf')):
                        f2.write(chunk)

                    shp_reader = shapefile.Reader(shp=f1, dbf=f2)
                    fields = shp_reader.fields[1:]
                    field_names = [field[0] for field in fields]
                    shp_buffer = []
                    for sr in shp_reader.shapeRecords():
                        atr = dict(zip(field_names, sr.record))
                        geom = sr.shape.__geo_interface__
                        shp_buffer.append(dict(type="Feature", geometry=geom, properties=atr))

            # Write the GeoJSON object
            geojson_str = json.dumps({"type": "FeatureCollection", "features": shp_buffer})
            '''
            End credit
            '''
            response_obj['proj_str'] = proj_str

        response_obj['success'] = 'Geojson obtained successfully.'
        response_obj['geojson_str'] = geojson_str
        response_obj['id'] = '%s:%s' % (res_id, filename)

    except Exception as e:
        print e
        response_obj['error'] = 'Failed to load watershed.'

    return response_obj
