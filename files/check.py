#!dev/bin/python


import os
import logging
import subprocess
import sys
import xml.etree.ElementTree as ET
from xml import etree
import ast
import traceback
import xmltodict
import json
#from telemtry import collect_sr, log_case_scc

f_handle = logging.FileHandler('./cluster-checker.log',mode='w')
f_format = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
f_handle.setFormatter(f_format)

logger = logging.getLogger(__name__)
logger.addHandler(f_handle)
logger.setLevel(logging.DEBUG)

def readingCib(path_to_scc):
    from lxml import etree # imported to use the enhanced parser in this library.
    #logger.info(str(output.communicate()))
    hostname_file = path_to_scc + '/etc/hostname'

    # Read the hostname from the file
    with open(hostname_file, 'r') as file:
        hostname = file.read().strip()

    # Construct the path to the cib.xml file
    path_to_xml = f"{path_to_scc}/sos_commands/pacemaker/crm_report/{hostname}/cib.xml"

    path_to_xml = path_to_scc + '/sos_commands/pacemaker/crm_report/' + hostname + '/cib.xml'
    parser = etree.XMLParser(recover=True)
    mycib = ET.parse(path_to_xml,parser=parser)
    ## to do  , rewrite teh code using a dictniary coded xml instead of parsing the xml itself in version 2
    #xml_string = ET.tostring(mycib.getroot()[0], encoding='UTF-8', method='xml')
    #dict_xml = xmltodict.parse(xml_string)
    #print(dict_xml)
    #return dict_xml
    return mycib.getroot()[0]

def propertyChecker(root_xml):
    root = root_xml
    logger.info(root)
    cluster_property = root[0][0]
    logger.info(cluster_property)

    node_list = []
    node_list_xml = root[1]
    azure_fence_agent = sbd_fence_agent = 0

    cluster_resources = root[2]
    fencing_resources = []
    for i in cluster_resources:
        if i.attrib.has_key('type'):
            if i.attrib['type'] == 'fence_azure_arm':
                fencing_resources.append('azure_fence_agent')
                azure_fence_agent = 1
            if i.attrib['type'] == 'external/sbd':
                fencing_resources.append('sbd')
                sbd_fence_agent = 1

    logger.info(f'Customer has the below fencing mechanism configured: {fencing_resources}')
    #print(f'Customer has the below fencing mechanism configured: {fencing_resources}')
    return azure_fence_agent, sbd_fence_agent
def SAPHanaChecker(resources):
    i = resources
    xml_string = ET.tostring(i, encoding='UTF-8', method='xml')
    dict_xml = xmltodict.parse(xml_string)
    printed=False
    #logger.info(i.attrib['id'])
    logger.info(dict_xml)
    #if i.attrib['id'].find('Topology') == -1:
    #logger.info('Customer have SAP hana cluster')
    #print('Customer have SAP hana cluster')
    #print(f'{dict_xml}')
    cluster_type='SAPHana'
    issues_config = {}
    #if i.attrib['id'].find('Topology') != -1:
    if 'clone' in dict_xml.keys() and dict_xml['clone']['@id'].find('Topology') != -1:
        issues_config[dict_xml['clone']['@id']] = []
        logger.info('Customer have SAP hana cluster')
        print('Customer have SAP hana cluster')
        printed=True
        #logger.info(i.attrib['id'])
        logger.info(dict_xml['clone']['@id'])
        logger.info('Checking on the topology resource metadata as per our documentation')
        #logger.info(i[0])
        #issues_dict['topology_metadata']={}
        #issues_dict['topology_operation']={}
        clone_node_max_dict = next((item for item in dict_xml['clone']['meta_attributes']['nvpair'] if item["@name"] == "clone-node-max"), None)
        interleave_dict = next((item for item in dict_xml['clone']['meta_attributes']['nvpair'] if item["@name"] == "interleave"), None)
        try:
            if clone_node_max_dict['@value'] != '1':
                issues_config[dict_xml['clone']['@id']].append(clone_node_max_dict)
            if interleave_dict['@value'] != 'true':
                issues_config[dict_xml['clone']['@id']].append(interleave_dict)
        except (TypeError, AttributeError) as e:
            issues_config[dict_xml['clone']['@id']].append(f"exception: {traceback.format_exc()}")

       # for j in i[0]:
       #     logger.info(j.attrib['name'])
       #     if j.attrib['name'] == 'clone-node-max' and j.attrib['value'] != "1":
       #         issues_dict['topology_metadata'].update({'clone-node-max' : j.attrib['value']})
       #     elif j.attrib['name'] == 'interleave' and j.attrib['value'] != 'true':
       #         issues_dict['topology_metadata'].update({'interleave' : j.attrib['value']})
        logger.info('Checking on the permittive on SAP Topology')
        logger.info(dict_xml['clone']['primitive']['operations']['op'])
        #logger.info(i[1].attrib['type'])
        monitor_dict = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "monitor"), None)
        start_dict = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "start"), None)
        stop_dict = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "stop"), None)
        try:
            if monitor_dict['@interval'] != '10' or monitor_dict['@timeout'] != '600':
                issues_config[dict_xml['clone']['@id']].append(monitor_dict)
            if start_dict['@interval'] != '0s' or start_dict['@timeout'] != '600':
                issues_config[dict_xml['clone']['@id']].append(start_dict)
            if stop_dict['@interval'] != '0s' or stop_dict['@timeout'] != '300':
                issues_config[dict_xml['clone']['@id']].append(stop_dict)
        except (TypeError, AttributeError) as e:
            issues_config[dict_xml['clone']['@id']].append(f"exception: {traceback.format_exc()}")
        #for j in i[1][0]:
        #    if j.attrib['name'] == 'monitor' and (j.attrib['interval'] != "10" or j.attrib['timeout'] != "600"):
        #            issues_dict['topology_operation'].update({'monitor' : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        #    if j.attrib['name'] == 'start' and (j.attrib['interval'] != "0" or j.attrib['timeout'] != "600"):
        #        issues_dict['topology_operation'].update({'start' : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        #    if j.attrib['name'] == 'stop' and (j.attrib['interval'] != "0" or j.attrib['timeout'] != "300"):
        #        issues_dict['topology_operation'].update({'stop' : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        if any(issues_config.values()):
            logger.info(f'SAP topology has issues below {issues_config}')
            print('\033[93m' + f'SAP topology has issues below {issues_config}' + '\033[0m')     
            print('\033[93m' + 'Please refer to documentation for the suggested values of timeout and interval: https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability-rhel' + '\033[0m')
        #if issues_dict['topology_metadata'] or issues_dict['topology_operation']:
        #    logger.info(f'SAP topology has issues below {issues_dict}')
        #    print(f'SAP topology has issues below {issues_dict}')
            

    #elif i.attrib['id'].find('SAPHana') != -1 and i.attrib['id'].find('Topology') == -1:
    elif 'clone' in dict_xml.keys() and dict_xml['clone']['@id'].find('SAPHana') != -1:
        issues_config[dict_xml['clone']['@id']] = []
        #if not printed:
        #    logger.info('Customer have SAP hana cluster')
        #    print('Customer have SAP hana cluster')
        logger.info(dict_xml['clone']['@id'])
        logger.info('Checking on the SAP resource as per our documentation')
        #issues_dict['Hana_metadata']={}
        #issues_dict['Hana_operation']={}
        #issues_dict['Hana_instance_attributes']={}
        #logger.info(i[0])
        
        notify_dict = next((item for item in dict_xml['clone']['meta_attributes']['nvpair'] if item["@name"] == "notify"), None)
        clone_max_dict = next((item for item in dict_xml['clone']['meta_attributes']['nvpair'] if item["@name"] == "clone-max"), None)
        clone_node_max_dict = next((item for item in dict_xml['clone']['meta_attributes']['nvpair'] if item["@name"] == "clone-node-max"), None)
        interleave_dict = next((item for item in dict_xml['clone']['meta_attributes']['nvpair'] if item["@name"] == "interleave"), None)
        try:
            if clone_max_dict['@value'] != '2':
                issues_config[dict_xml['clone']['@id']].append(clone_max_dict)
            if clone_node_max_dict['@value'] != '1':
                issues_config[dict_xml['clone']['@id']].append(clone_node_max_dict)
            if notify_dict['@value'] != 'true':
                issues_config[dict_xml['clone']['@id']].append(notify_dict)
            if interleave_dict['@value'] != 'true':
                issues_config[dict_xml['clone']['@id']].append(interleave_dict)
        except (TypeError, AttributeError) as e:
            issues_config[dict_xml['clone']['@id']].append(f"exception: {traceback.format_exc()}")

        #for j in i[0]:
        #    logger.info(j.attrib['name'])
        #    if j.attrib['name'] == 'clone-node-max' and j.attrib['value'] != "1":
        #        issues_dict['Hana_metadata'].update({j.attrib['name'] : j.attrib['value']})
        #    elif j.attrib['name'] == 'interleave' and j.attrib['value'] != 'true':
        #        issues_dict['Hana_metadata'].update({j.attrib['name'] : j.attrib['value']})
        #    elif j.attrib['name'] == 'is-managed' and j.attrib['value'] != 'true':
        #        issues_dict['Hana_metadata'].update({j.attrib['name'] : j.attrib['value']})
        #    elif j.attrib['name'] == 'notify' and j.attrib['value'] != 'true':
        #        issues_dict['Hana_metadata'].update({j.attrib['name'] : j.attrib['value']})
        #    elif j.attrib['name'] == 'clone-max' and j.attrib['value'] != '2':
        #        issues_dict['Hana_metadata'].update({j.attrib['name'] : j.attrib['value']})                
        
        logger.info('Checking on the permittive of SAP Hana')
        logger.info(dict_xml['clone']['primitive']['operations']['op'])
        master_monitor = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "monitor" and item['@role'] == 'Master'), None)
        slave_monitor = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "monitor" and item['@role'] == 'Slave'), None)
        start_dict = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "start"), None)
        stop_dict = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "stop"), None)
        promote_dict = next((item for item in dict_xml['clone']['primitive']['operations']['op'] if item["@name"] == "promote"), None)
        try:
            if master_monitor['@name'] == 'monitor' and master_monitor['@role'] == 'Master' and (master_monitor['@interval'] != "59" or master_monitor['@timeout'] != "700"):
                issues_config[dict_xml['clone']['@id']].append(master_monitor)
            if slave_monitor['@name'] == 'monitor' and slave_monitor['@role'] == 'Slave' and (slave_monitor['@interval'] != "61" or slave_monitor['@timeout'] != "700"):
                issues_config[dict_xml['clone']['@id']].append(slave_monitor)
            if start_dict['@name'] == 'start' and (start_dict['@interval'] != "0s" or start_dict['@timeout'] != "3600"):
                issues_config[dict_xml['clone']['@id']].append(start_dict)
            if stop_dict['@name'] == 'stop' and (stop_dict['@interval'] != "0s" or stop_dict['@timeout'] != "3600"):
                issues_config[dict_xml['clone']['@id']].append(stop_dict)
            if promote_dict['@name'] == 'promote' and (promote_dict['@interval'] != "0s" or promote_dict['@timeout'] != "3600"):
                issues_config[dict_xml['clone']['@id']].append(promote_dict)
        except (TypeError, AttributeError) as e:
            issues_config[dict_xml['clone']['@id']].append(f"exception: {traceback.format_exc()}")
        #logger.info(i[1].attrib['id'])
        #logger.info(i[1].attrib['type'])
        #for j in i[1][0]:
        #    if j.attrib['name'] == 'monitor' and j.attrib['role'] == 'clone' and (j.attrib['interval'] != "60" or j.attrib['timeout'] != "700"):
        #        issues_dict['Hana_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        #    if j.attrib['name'] == 'monitor' and j.attrib['role'] == 'Slave' and (j.attrib['interval'] != "61" or j.attrib['timeout'] != "700"):
        #        issues_dict['Hana_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        #    if j.attrib['name'] == 'start' and (j.attrib['interval'] != "0" or j.attrib['timeout'] != "3600"):
        #        issues_dict['Hana_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        #    if j.attrib['name'] == 'stop' and (j.attrib['interval'] != "0" or j.attrib['timeout'] != "3600"):
        #        issues_dict['Hana_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        #    if j.attrib['name'] == 'promote' and (j.attrib['interval'] != "0" or j.attrib['timeout'] != "3600"):
        #        issues_dict['Hana_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
        
        logger.info('Checking on the instance_attributes of SAP Hana')
        logger.info(dict_xml['clone']['primitive']['instance_attributes'])
        temp_dict={}
        for j in dict_xml['clone']['primitive']['instance_attributes']['nvpair']:
            if j['@name'] == 'PREFER_SITE_TAKEOVER' and j['@value'] != 'true':
                temp_dict[j['@name']] = j['@value']
                issues_config[dict_xml['clone']['@id']].append(temp_dict)
            if j['@name'] == 'DUPLICATE_PRIMARY_TIMEOUT' and j['@value'] != '7200':
                temp_dict[j['@name']] = j['@value']
                issues_config[dict_xml['clone']['@id']].append(temp_dict)
            if j['@name'] == 'SID':
                sid = j['@value']
            if j['@name'] == 'InstanceNumber':
                instanceNumber = j['@value']
            if j['@name'] == 'AUTOMATED_REGISTER':
                auto_register = j['@value']
        
        logger.info(f'Customer has database of name {sid} and instance number {instanceNumber}, please also note that the vaule for AUTOMATED_REGISTER is' + '\033[93m' + f' {auto_register}' + '\033[0m')
        print(f'Customer has database of name {sid} and instance number {instanceNumber}, please also note that the vaule for AUTOMATED_REGISTER is' + '\033[93m' + f' {auto_register}' + '\033[0m')

        #if issues_dict['Hana_metadata'] or issues_dict['Hana_operation']:
        if any(issues_config.values()):
            logger.info(f'SAP Hana has issues below {issues_config}')
            print('\033[93m' + f'SAP Hana has issues below {issues_config}' + '\033[0m')     
            print('\033[93m' + 'Please refer to documentation for the suggested values of timeout and interval: https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability-rhel' + '\033[0m')
            #logger.info(f'SAP Hana has issues below {issues_config}')
            #print(f'SAP Hana has issues below {issues_config}')

def ASCSGroupChecker(resources):
    i = resources
    fs_issues={}
    logger.info(i.attrib['id'])
    logger.info('Customer have ASCS/ERS cluster')
    print('Customer have ASCS/ERS cluster')
    logger.info('Start checking on the ASCS resource group')
    for resource in i:
        if 'type' in resource.keys():
            #print(type(resource.attrib['type']))
            if resource.attrib['type'] == 'Filesystem':
                logger.info('Start checking on ASCS file system all details')
                fs_issues['ascs_fs_operation']={}
                logger.info(f'Resource name checking is {resource.attrib["id"]}')
                logger.info('Checking on instance_attributes')
                for j in resource[0]:
                    if j.attrib['name'] == 'device':
                        device=j.attrib['value']
                    elif j.attrib['name'] == 'directory':
                        mountpoint=j.attrib['value']
                    elif j.attrib['name'] == 'fstype':
                        fstype=j.attrib['value']
                logger.info('\033[93m' + f'ASCS file system is {fstype}, and the source device is {device} and mounted on {mountpoint}'+'\033[0m')
                print('\033[93m' + f'ASCS file system is {fstype}, and the source device is {device} and mounted on {mountpoint}'+'\033[0m')
                logger.info('Checking file system operation parameters:')
    #            for j in resource[1]:
    #                if j.attrib['name'] == 'monitor' and (j.attrib['interval'].find('20') == -1 or j.attrib['timeout'].find('40') == -1 ):
    #                    fs_issues['ascs_fs_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
    #                if j.attrib['name'] == 'start' and (j.attrib['interval'] != "0" or j.attrib['timeout'].find('60') == -1):
    #                    fs_issues['ascs_fs_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
    #                if j.attrib['name'] == 'stop' and (j.attrib['interval'] != "0" or j.attrib['timeout'].find('120') == -1):
    #                    fs_issues['ascs_fs_operation'].update({j.attrib['name'] : { 'interval': j.attrib['interval'] , 'timeout' : j.attrib['timeout'] }})
                for j in resource[1]:
                    if j.attrib['name'] == 'monitor' and (int(j.attrib['interval']) != 200 or int(j.attrib['timeout']) != 40):
                        fs_issues['ascs_fs_operation'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})
                    if j.attrib['name'] == 'start' and (int(j.attrib['interval']) != 0 or int(j.attrib['timeout']) != 60):
                        fs_issues['ascs_fs_operation'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})
                    if j.attrib['name'] == 'stop' and (int(j.attrib['interval']) != 0 or int(j.attrib['timeout']) != 120):
                        fs_issues['ascs_fs_operation'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})

                
                if fs_issues['ascs_fs_operation']:
                    logger.info(f'ASCS file system resource has following issues {fs_issues}')
                    print(f'ASCS file system resource has following issues {fs_issues}')

            elif resource.attrib['type'] == 'anything' or resource.attrib['type'] == 'azure-lb':
                if resource.attrib['type'] == 'anything':
                    logger.info('Customer is using socat or nc for load balancer probing')
                    for j in resource[0]:
                        if j.attrib['name'] == 'binfile':
                            command = j.attrib['value']
                        if j.attrib['name'] == 'cmdline_options':
                            options = j.attrib['value']
                    logger.info('\033[93m' + f'cusotmer is using command {command} with the following options {options} for azure load balancer probing for ASCS'+'\033[0m')
                    print('\033[93m' + f'cusotmer is using command {command} with the following options {options} for azure load balancer probing for ASCS'+'\033[0m')
                    fs_issues['socat_operations']={}
                    if resource[1][0].attrib['name'] == 'monitor' and (resource[1][0].attrib['interval'].find('10') == -1 or resource[1][0].attrib['timeout'].find('20') == -1 ):
                        fs_issues['socat_operations'].update({resource[1][0].attrib['name'] : { 'interval': resource[1][0].attrib['interval'] , 'timeout' : resource[1][0].attrib['timeout'] }})
                    
                    if fs_issues['socat_operations']:
                        logger.info(f'ASCS Azure lb has the following issues {fs_issues}')
                        print(f'ASCS Azure lb has the following issues {fs_issues}')  

                else:
                    logger.info('Customer is using azure-lb')
                    print('Customer is using azure-lb for load balancer probing')

            elif resource.attrib['type'] == 'SAPInstance':
                logger.info('Checking on ASCS resource and starting with operations')
                fs_issues['ascs_operations'] = {}
                instance_attributes = resource.find('instance_attributes')
                operations = resource.find('operations')

                if operations is not None:
                    for j in operations:
                        #print(f'{j.attrib}')
                        if j.attrib['name'] == 'monitor' and (j.attrib['interval'] != '20' or j.attrib['timeout'] != '60'):
                            fs_issues['ascs_operations'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})

                    if fs_issues['ascs_operations']:
                        logger.info(f'ASCS resource has the following issues on operations {fs_issues}')
                        print(f'ASCS resource has the following issues on operations {fs_issues}')

                logger.info('Moving to check on the instance metadata information for ASCS')
                if instance_attributes is not None:
        # Checking instance metadata information for the SAPInstance resource
                    instanceName = startProfile = recoverState = None
                    for j in instance_attributes:
                        if j.attrib['name'] == 'InstanceName':
                            instanceName = j.attrib['value']
                        elif j.attrib['name'] == 'START_PROFILE':
                            startProfile = j.attrib['value']
                        elif j.attrib['name'] == 'AUTOMATIC_RECOVER':
                            recoverState = j.attrib['value']

                    logger.info(f'ASCS instance name {instanceName} and the start profile is located under {startProfile} and automatic recover is set to {recoverState}')
                    print(f'ASCS instance name {instanceName} and the start profile is located under {startProfile} and automatic recover is set to {recoverState}')



def ERSGroupChecker(resources):
    i = resources
    fs_issues={}
    logger.info(i.attrib['id'])
    logger.info('Customer have ASCS/ERS cluster')
    #print('Customer have ASCS/ERS cluster')
    logger.info('Start checking on the ERS resource group')
    for resource in i:
        if 'type' in resource.keys():
            #print(type(resource.attrib['type']))
            if resource.attrib['type'] == 'Filesystem':
                logger.info('Start checking on ERS file system all details')
                fs_issues['ers_fs_operations']={}
                logger.info(f'Resource name checking is {resource.attrib["id"]}')
                logger.info('Checking on instance_attributes')
                for j in resource[0]:
                    if j.attrib['name'] == 'device':
                        device=j.attrib['value']
                    elif j.attrib['name'] == 'directory':
                        mountpoint=j.attrib['value']
                    elif j.attrib['name'] == 'fstype':
                        fstype=j.attrib['value']
                logger.info('\033[93m' + f'ERS file system is {fstype}, and the source device is {device} and mounted on {mountpoint}'+'\033[0m')
                print('\033[93m' + f'ERS file system is {fstype}, and the source device is {device} and mounted on {mountpoint}'+'\033[0m')
                logger.info('Checking file system operation parameters:')
                
                for j in resource[1]:
                    if j.attrib['name'] == 'monitor' and (int(j.attrib['interval']) != 200 or int(j.attrib['timeout']) != 40):
                        fs_issues['ers_fs_operations'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})
                    if j.attrib['name'] == 'start' and (int(j.attrib['interval']) != 0 or int(j.attrib['timeout']) != 60):
                        fs_issues['ers_fs_operations'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})
                    if j.attrib['name'] == 'stop' and (int(j.attrib['interval']) != 0 or int(j.attrib['timeout']) != 120):
                        fs_issues['ers_fs_operations'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})

                if fs_issues['ers_fs_operations']:
                    logger.info(f'ERS file system resource has following issues {fs_issues}')
                    print(f'ERS file system resource has following issues {fs_issues}')

            elif resource.attrib['type'] == 'anything' or resource.attrib['type'] == 'azure-lb':
                if resource.attrib['type'] == 'anything':
                    logger.info('Customer is using socat or nc for load balancer probing')
                    for j in resource[0]:
                        if j.attrib['name'] == 'binfile':
                            command = j.attrib['value']
                        if j.attrib['name'] == 'cmdline_options':
                            options = j.attrib['value']
                    logger.info('\033[93m' + f'cusotmer is using command {command} with the following options {options} for azure load balancer probing for ERS'+'\033[0m')
                    print('\033[93m' + f'cusotmer is using command {command} with the following options {options} for azure load balancer probing for ERS'+'\033[0m')
                    fs_issues['socat_operations']={}
                    if resource[1][0].attrib['name'] == 'monitor' and (resource[1][0].attrib['interval'].find('10') == -1 or resource[1][0].attrib['timeout'].find('20') == -1 ):
                        fs_issues['socat_operations'].update({resource[1][0].attrib['name'] : { 'interval': resource[1][0].attrib['interval'] , 'timeout' : resource[1][0].attrib['timeout'] }})

                    if fs_issues['socat_operations']:
                        logger.info(f'ERS Azure lb has the following issues {fs_issues}')
                        print(f'ERS Azure lb has the following issues {fs_issues}')

                else:
                    logger.info('Customer is using azure-lb')
                    print('Customer is using azure-lb for load balancer probing')

            elif resource.attrib['type'] == 'SAPInstance':
                logger.info('Checking on ERS resource and start with operations')
                fs_issues['ers_operations'] = {}
                instance_attributes = resource.find('instance_attributes')
                operations = resource.find('operations')

                if operations is not None:
                    for j in operations:
                        #print(f'{j.attrib}')
                        if j.attrib['name'] == 'monitor' and (j.attrib['interval'] != '20' or j.attrib['timeout'] != '60'):
                            fs_issues['ers_operations'].update({j.attrib['name']: {'interval': j.attrib['interval'], 'timeout': j.attrib['timeout']}})

                    if fs_issues['ers_operations']:
                        logger.info(f'ERS resource has the following issues on operations {fs_issues}')
                        print(f'ERS resource has the following issues on operations {fs_issues}')

                logger.info('Moving to check on the instance metadata information for ERS')
                if instance_attributes is not None:
                    for j in instance_attributes:
                        if j.attrib['name'] == 'InstanceName':
                            instanceName = j.attrib['value']
                        elif j.attrib['name'] == 'START_PROFILE':
                            startProfile = j.attrib['value']
                        elif j.attrib['name'] == 'AUTOMATIC_RECOVER':
                            recoverState = j.attrib['value']
                        elif j.attrib['name'] == 'IS_ERS':
                            isERS = j.attrib['value']

                    logger.info(f'ERS instance name {instanceName} and the start profile is located under {startProfile} and automatic recover is set to {recoverState} and has IS_ERS set to {isERS}')
                    print(f'ERS instance name {instanceName} and the start profile is located under {startProfile} and automatic recover is set to {recoverState} and has IS_ERS set to {isERS}')




def getClusterType(root_xml):
    cluster_resources = root_xml[2]
    logger.info(cluster_resources)
    cluster_type=""
    #issues_dict = {}


    for i in cluster_resources:
        if i.attrib['id'].find('SAPHana') != -1:
            cluster_type="SAPCluster"
            SAPHanaChecker(i)

        elif i.attrib['id'].find('ASCS') != -1 or i.attrib['id'].find('ERS') != -1:
            logger.info(i.attrib['id'])
            cluster_type='ASCSERS'
            if i.attrib['id'].find('ASCS') != -1:
                ASCSGroupChecker(i)
            elif i.attrib['id'].find('ERS') != -1:
                ERSGroupChecker(i)

    return cluster_type
def constrainsChecker(root_xml, cluster_type):
    cluster_contrains = root_xml[3]
    try:
        xml_string = ET.tostring(cluster_contrains, encoding='UTF-8', method='xml')
        dict_xml = xmltodict.parse(xml_string)
        logger.info('Start checking on the constrains')
        logger.info('Checking on location constraints if they have cli-prefer and point them out')
        location_constraints = dict_xml['constraints']['rsc_location']
        logger.info(location_constraints)
        if type(location_constraints) is list:
            if len(location_constraints) >= 1:
                for i in location_constraints:
                    if i['@id'].find('cli-prefer') != -1:
                        logger.info(f'below constraint {i["@id"]} was created from crm cli, please check if this contribute to the issue you are investgating')
                        print(f'below constraint {i["@id"]} was created from crm cli, please check if this contribute to the issue you are investgating')
        else:
            if location_constraints['@id'].find('cli-prefer') != -1:
                logger.info(f'below constraint {i["@id"]} was created from crm cli, please check if this contribute to the issue you are investgating')
                print(f'below constraint {i["@id"]} was created from crm cli, please check if this contribute to the issue you are investgating')
                
        logger.info(f'Determining the type of cluster {cluster_type}')
        if cluster_type == 'SAPCluster':
            logger.info(dict_xml)
            print(f'{dict_xml}')
            logger.info('Checking on colocation constraint')
            colocation_constraint = dict_xml['constraints']['rsc_colocation']
            if (colocation_constraint['@score'] != '4000' or 
                (colocation_constraint['@rsc'].find('g_') == -1 and colocation_constraint['@rsc-role'] != 'Started')
                or (colocation_constraint['@with-rsc'].find('msl_') == -1 and colocation_constraint['@with-rsc-role'] != 'Master')):
                logger.info(f'Colocation constraints have issue {colocation_constraint}')
                print('Checking on colocaiton constraints, and we found that it is not following our documentation: https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability-rhel')
                print(f'Colocation constraints has the following incorrect configuration {colocation_constraint}')
            else:
                logger.info(f'No issues found on the colocation constraints of id {colocation_constraint["@id"]}')
                print(f'No issues found on the colocation constraints of id {colocation_constraint["@id"]}')
            
            logger.info('checking on the order constrains')
            order_constraint = dict_xml['constraints']['rsc_order']
            if (order_constraint['@kind'] != 'Optional' or order_constraint['@first'].find('cln_') == -1 
            or order_constraint['@then'].find('msl_') == -1):
                logger.info(f'order constraints have issue {order_constraint}')
                print('Checking on order constraints, and we found that it is not following our documentation: https://learn.microsoft.com/en-us/azure/sap/workloads/sap-hana-high-availability-rhel')
                print(f'order constraints has the following incorrect configuration {order_constraint}')
            else:
                logger.info(f'No issues found on the order constraints of id {order_constraint["@id"]}')
                print(f'No issues found on the order constraints of id {order_constraint["@id"]}')

        elif cluster_type == 'ASCSERS':
            logger.info(dict_xml)
            logger.info('Checking on colocation constraints')
            colocation_constraint = dict_xml['constraints']['rsc_colocation']
            if(colocation_constraint['@score'] != '-5000' or colocation_constraint['@rsc'].find('ERS') == -1 
                or colocation_constraint['@with-rsc'].find('ASC') == -1):
                logger.info(f'Colocation constraints have issue {colocation_constraint}')
                print('Checking on colocaiton constraints, and we found that it is not following our documentation: https://learn.microsoft.com/en-us/azure/sap/workloads/high-availability-guide-rhel-nfs-azure-files')
                print(f'Colocation constraints has the following incorrect configuration {colocation_constraint}')
            else:
                logger.info(f'No issues found on the colocation constraints of id {colocation_constraint["@id"]}')
                print(f'No issues found on the colocation constraints of id {colocation_constraint["@id"]}')

            logger.info('checking on the order constrains')
            order_constraint = dict_xml['constraints']['rsc_order']
            if(order_constraint['@kind'] != 'Optional' or order_constraint['@symmetrical'] != 'false'
                or (order_constraint['@first'].find('ASCS') == -1 and order_constraint['@first-action'] != 'start')
                or (order_constraint['@then'].find('ERS') == -1 and order_constraint['@then-action'] != 'stop')):
                logger.info(f'order constraints have issue {order_constraint}')
                print('Checking on order constraints, and we found that it is not following our documentation: https://learn.microsoft.com/en-us/azure/sap/workloads/high-availability-guide-rhel-nfs-azure-files')
                print(f'order constraints has the following incorrect configuration {order_constraint}')
            else:
                logger.info(f'No issues found on the order constraints of id {order_constraint["@id"]}')
                print(f'No issues found on the order constraints of id {order_constraint["@id"]}')

            logger.info('checking on the location constrains')
            logger.info('As per doc update, there could be no location constrains configured for new version of SAP, so confirming that this location constrains is not CLI related')
            print('Please check if there is a location constrains configured (does not have cli-prefer in its name) in case customer using old ASCS/ERS infra, as the new version does not require this locaion constraint')
            # to do to add the location constraints checker
            #location_constraints = dict_xml['constraints']['rsc_location']
            #if location_constraints['@id'].find('cli-prefer') == -1:
            #    logger.info('This location constrains is not CLI related')
            #    if ():

    except (TypeError, AttributeError, KeyError) as e:
        print('\033[91m' + 'There was an exception on checking on the constrains, please check on that manually as there could be some comments on the configration that causing this issue' + '\033[0m')
        logger.warning(f'exception:{traceback.format_exc()}')

if __name__ == '__main__':
    raw_args = sys.argv
    while True:
        if len(raw_args) <= 1 :
            logger.info('Please provide the path to scc report')
            path_to_scc= input('Please provide the path to scc report (either relative or absolute)')
            if path_to_scc is None or len(path_to_scc.split('/')) < 2:
                continue
            break
        else:
            path_to_scc = raw_args[1]
            break
    if path_to_scc.find('.txz') != -1:
        logger.info('This is a compressed file, extracting it')
        print('Extracting scc report ...')
        extract_file = 'tar xf '+path_to_scc
        output = subprocess.Popen([extract_file], stdout=subprocess.PIPE, shell=True)
        logger.info(output.communicate())
        path_to_scc = path_to_scc.split('.')[0]
        logger.info(f'Path to scc is {path_to_scc}')
    #sr_num = collect_sr()
    logger.info(path_to_scc)
    #log_case_scc(sr_num, path_to_scc)
    #if  readingCib(path_to_scc):
    if len(readingCib(path_to_scc)) > 0:
        root_xml = readingCib(path_to_scc)
        azure_fence_agent, sbd_fence_agent = propertyChecker(root_xml)
        cluster_type = getClusterType(root_xml)
        constrainsChecker(root_xml, cluster_type)

