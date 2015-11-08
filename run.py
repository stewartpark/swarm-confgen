from docker import Client
from mako.template import Template
import yaml
import os

DOCKER_HOST = os.environ.get('DOCKER_HOST', "unix://var/run/docker.sock")
swarm = Client(base_url=DOCKER_HOST)
config = yaml.load(open('confgen.yml'))
cmdlines_to_run = []


def run(cmdline):
    """Schedule a command line after config generation."""
    cmdlines_to_run.append(cmdline)


if __name__ == "__main__":
    apps = []
    service_ports = set()
    for app_name in config:
        apps.append(dict(
            name=app_name,
            containers=swarm.containers(
                filters=config[app_name]['containers']
            ),
            domain=config[app_name]['domain'],
            port=config[app_name]['port']
        ))
        service_ports.add(config[app_name]['port'])

    print '[+] Generating config files...'
    os.chdir('src')
    for path, dirs, files in os.walk("."):
        for fn in files:
            realpath = os.path.join(path[1:], fn)
            print ' - %s' % realpath
            template = Template(open("." + realpath).read())
            text = template.render(apps=apps, service_ports=service_ports, run=run)
            try:
                f = open(realpath, "w+")
                f.write(text)
                f.close()
                print '   => Done.'
            except:
                print '   => Failed.'
                print text
    print '[+] Refreshing services...'
    for cmdline in cmdlines_to_run:
        print ' - "%s"' % cmdline
        os.system(cmdline)
