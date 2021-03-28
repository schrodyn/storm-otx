#
#####
# Section One

# Service Information
svc_name = 'otx'
svc_guid = 'c339177577d0a7a76b3df08fff1da7cb'
svc_vers = (0, 0, 1)

# Create a source to represent this service.
svc_evts = {
    'add': {
        'storm': f'[(meta:source={svc_guid} :name="OTX data")]'
    }
}

##### Section Two
# Section Two

# This is the storm used to ingest the data.
svc_mod_ingest_storm = '''
function ingest_dns(data, srcguid) {

    $results = $lib.set()

    for ($type, $value, $seen_first, $seen_last) in $data {

        // $lib.print("otx->svc_mod_ingest_storm type: {data}", data=$type)
        // $lib.print("otx->svc_mod_ingest_storm value: {data}", data=$value)
        // $lib.print("otx->svc_mod_ingest_storm first: {data}", data=$seen_first)
        // $lib.print("otx->svc_mod_ingest_storm last: {data}", data=$seen_last)

        switch $type {

            NS: {
                [ inet:dns:ns = $value ]

                { +inet:dns:ns $results.add($node) }
            }

            CNAME: {
                [ inet:dns:cname = $value ]

                { +inet:dns:cname $results.add($node) }
            }

            A: {
                [ inet:dns:a = $value ]

                { +inet:dns:a $results.add($node) }
            }

            AAAA: {
                [ inet:dns:aaaa = $value ]

                { +inet:dns:aaaa $results.add($node) }
            }
        }

        { [.seen=( $seen_first, $seen_last )] }

        // Lightweight edge back to meta:source
        { [ <(seen)+ { meta:source=$srcguid } ] }
    }

    | spin |

    return($results)
}
'''

#####
# Section Three - Help Information and command args.

# The first line of this description will display in the Storm help
# OTX Domain command description.
svc_cmd_pdns_desc = '''
Query the Alienvault OTX API service for passive DNS.

Examples:

    # Query the service
    inet:fqdn=good.com | otx.pdns
    inet:ipv4=1.1.1.1 | otx.pdns
    inet:ipv6=::1 | otx.pdns

    # Query the service and yield the created inet:dns:a node
    inet:fqdn=good.com | otx.pdns --yield
'''

svc_cmd_domain_forms = {
    'input': [
        'inet:fqdn',
        'inet:ipv4',
        'inet:ipv6',
    ],
    'output': [
        'inet:dns:a',
    ],
}

svc_cmd_args = (
    ('--yield', {'default': False, 'action': 'store_true',
                 'help': 'Whether to yield the created nodes to the output stream.'}),
    ('--debug', {'default': False, 'action': 'store_true',
                 'help': 'Enable debug output.'}),
    ('--apikey', {'required': True, 'help': 'OTX API Key.'}),
    ('--hostname', {'default': False, 'action': 'store_true',
                 'help': 'Query the Hostname API endpoint rather than the Domain endpoint.'}),
)

svc_cmd_conf = {
    'srcguid': svc_guid,
}

#####
# Section Four - command specific storms

##### Storm for the domain command.
svc_cmd_pdns_storm = '''
init {
    $svc = $lib.service.get($cmdconf.svciden)

    // Call domain only ingest???
    $ingest = $lib.import(otx.ingest)

    $srcguid = $cmdconf.srcguid
    $debug = $cmdopts.debug
    $yield = $cmdopts.yield
    $apikey = $cmdopts.apikey
    $hostname = $cmdopts.hostname
}

// $node is a special variable that references the inbound Node object
$form = $node.form()

switch $form {
    "inet:fqdn": {
        $query=$node.repr()
        $ioc_type="fqdn"
    }
    "inet:ipv4": {
        $query=$node.repr()
        $ioc_type="ipv4"
    }
    "inet:ipv6": {
        $query=$node.repr()
        $ioc_type="ipv6"
    }
    *: {
        $query=""
        $lib.warn("OTX service does not support {form} nodes", form=$form)
    }
}

// Yield behavior to drop the inbound node
if $yield { spin }

// Call the service endpoint and ingest the results
if $query {

    if $debug { $lib.print("otx query: {query}", query=$query) }

    // $iszone=$node.repr(iszone)

    // if $debug { $lib.print("otx iszone: {iszone}", iszone=$iszone) }

    if $debug { $lib.print("otx apikey: {apikey}", apikey=$apikey) }

    // Call function for FQDN pDNS data.
    $retn = $svc.getPDNSData($apikey, $ioc_type, $query, $hostname)

    if $retn.status {
        $results = $ingest.ingest_dns($retn.data, $srcguid)

        if $yield {
            for $result in $results { $lib.print($result) yield $result }
        }
    } else {
        $lib.warn("otx error: {err}", err=$retn.mesg)
    }
}
'''

#####
# Section Five
svc_cmds = (
    # Domain Passive DNS Command
    {
        'name': f'{svc_name}.pdns',
        'descr': svc_cmd_pdns_desc,
        'cmdargs': svc_cmd_args,
        'cmdconf': svc_cmd_conf,
        'forms': svc_cmd_domain_forms,
        'storm': svc_cmd_pdns_storm,
    },
    # Hostname Command
    # IPv4 Command
    # IPv6 Command
)

svc_pkgs = (
    {
        'name': svc_name,
        'version': svc_vers,
        'modules': (
            {
                # Used in svc_cmds - storm
                'name': f'{svc_name}.ingest',
                'storm': svc_mod_ingest_storm,
            },
        ),
        'commands': svc_cmds,
    },
)
