import sys
import asyncio
import logging

from enum import Enum

import synapse.lib.cell as s_cell
import synapse.lib.stormsvc as s_stormsvc

from storm import *
from OTXv2 import OTXv2
from OTXv2 import IndicatorTypes

logger = logging.getLogger(__name__)

class IOCType(Enum):
    fqdn = IndicatorTypes.DOMAIN
    ipv4 = IndicatorTypes.IPv4
    ipv6 = IndicatorTypes.IPv6

class OtxApi(s_cell.CellApi, s_stormsvc.StormSvc):
    '''
    A Telepath API for the OTX service.
    '''

    # These defaults must be overridden from the StormSvc mixin
    _storm_svc_name = svc_name
    _storm_svc_vers = svc_vers
    _storm_svc_evts = svc_evts
    _storm_svc_pkgs = svc_pkgs

    async def getPDNSData(self, apikey, ioc_type, query, hostname: False):
        return await self.cell.getPDNSData(apikey, ioc_type, query,
                hostname)

    async def getInfo(self):
        await self._reqUserAllowed(('otx', 'info'))
        return await self.cell.getInfo()

    @s_cell.adminapi()
    async def getAdminInfo(self):
        return await self.cell.getAdminInfo()

class Otx(s_cell.Cell):

    cellapi = OtxApi

    confdefs = {}

    async def __anit__(self, dirn, conf):
        await s_cell.Cell.__anit__(self, dirn, conf=conf)

    async def getPDNSData(self, apikey, ioc_type, query, hostname):

        otx_ioc_type = None

        apiclient = OTXv2(apikey)

        # Best practice is to also return a status and optional message in case of an error
        retn = {
            'status': True,
            'data': None,
            'mesg': None,
        }

        otx_ioc_type = IOCType[ioc_type].value

        if hostname:
            otx_ioc_type = IndicatorTypes.HOSTNAME

        try:
            otx_data = apiclient.get_indicator_details_by_section(
                    otx_ioc_type, query, 'passive_dns')
        except Exception as exc:
            logger.error("Error retrieving OTX data")
            logger.error("%s", exc)
            retn['status'] = False
            retn['mesg'] = 'An error occurred during data retrieval.'
        else:

            # Retrieving and parsing data would go here
            if otx_data:

                data = []

                if 'passive_dns' in otx_data and otx_data['passive_dns']:

                    pdns_data = otx_data['passive_dns']

                    for result in pdns_data:

                        rdata = result['address']

                        if rdata == 'NXDOMAIN':
                            continue

                        rrname = result['hostname']

                        if rrname == rdata:
                            logging.info("Matching values, probably OTX bug.")
                            logging.info("rrname: %s -> rdata: %s",
                                    rrname, rdata)
                            continue

                        rrtype = result['record_type']
                        seen_first = result['first']
                        seen_last = result['last']

                        if seen_first == seen_last:
                            seen_last = '?'

                        data.append((rrtype, (rrname, rdata),
                            seen_first, seen_last))
                else:
                    retn['mesg'] = 'No passive DNS data results.'

                retn['data'] = data

        return retn

    async def getInfo(self):
        info = {
            'generic': 'info',
        }

        return info

    async def getAdminInfo(self):
        info = {
            'admin': 'info',
        }

        return info
