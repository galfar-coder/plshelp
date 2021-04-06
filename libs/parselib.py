from configparser import ConfigParser


# noinspection PyTypeChecker
class Parse:
    def __init__(self, filename):
        """Parses the minecraft logs and returns the results in a dict."""
        with open(filename, "r") as f:
            self.subject = f.readlines()
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.blacklist = self.config['PARSER']['WordIndexBlacklist'].split(",")
        self.errorblacklist = self.config['PARSER']['ErrorBlacklist'].split(",")
        self.errorwhitelist = self.config['PARSER']['ErrorWhitelist'].split(",")
        self.results = {
            "plugins": [],
            "plugins_altver": [],
            "errors": [],
            "classified_errors": {},
            "common_errors": []
        }

    def analysis(self):
        start_exception_linecnt = False
        exception_linecnt = 0
        for i in self.subject:
            try:
                if start_exception_linecnt is True:
                    if exception_linecnt <= 6:
                        if "\tat " in i or "java.lang" in i:
                            self.results["errors"].append(i.rstrip("\n").replace("\t", ""))
                            exception_linecnt += 1
                            continue
                        else:
                            start_exception_linecnt = False
                    else:
                        start_exception_linecnt = False
                if 'Starting minecraft server version' in i:
                    self.results["minecraft_version"] = i.split("Starting minecraft server version ")[1].rstrip("\n")
                elif 'This server is running' in i and 'version' in i:
                    self.results["server_software"] = i.split(" version ")[1].split(" (MC: ")[0].rstrip("\n")
                elif '] Loading ' in i and " v" in i:
                    try:
                        for x in self.blacklist:
                            if x in i:
                                raise ValueError
                        if i.split('] Loading ')[1].rstrip("\n") in self.results["plugins"]:
                            continue
                        if i.split('] Loading ')[1].split(' v')[0].rstrip("\n") in self.results["plugins_altver"]:
                            continue
                        self.results["plugins"].append(i.split('] Loading ')[1].rstrip("\n"))
                        self.results["plugins_altver"].append(i.split('] Loading ')[1].split(' v')[0].rstrip("\n"))
                    except ValueError:
                        continue
                elif 'generated an exception' in i or "Could not pass event" in i or 'Exception' in i or "Could not " \
                                                                                                         "load '" in i:
                    try:
                        for x in self.errorblacklist:
                            if x in i:
                                raise ValueError
                        self.results["errors"].append(i.rstrip("\n").replace("\t", ""))
                        start_exception_linecnt = True
                        exception_linecnt = 0
                    except ValueError:
                        continue
                elif 'Server thread/ERROR' in i:
                    try:
                        for x in self.errorblacklist:
                            if x in i:
                                raise ValueError
                        self.results["errors"].append(i.rstrip("\n"))
                    except ValueError:
                        continue
                elif '/rl' in i or '/reload' in i:
                    self.results['reload'] = True
                elif 'UnsupportedClassVersionError' in i and 'this version of the Java Runtime only recognizes class ' \
                                                             'file versions up to 52.0' in i:
                    self.results['needs_newer_java'] = True
                elif 'Server thread/WARN' in i:
                    for x in self.errorwhitelist:
                        if x in i:
                            self.results["errors"].append(i.rstrip("\n"))

                if 'Wrong shop.yml/shop.groovy configuration!' in i:
                    self.results["sbw_wrongshop"] = True
            except AttributeError:
                continue
        self.check_defaults_bool('needs_newer_java')
        self.check_defaults_bool('reload')
        self.check_defaults_bool('sbw_wrongshop')
        self.check_defaults('minecraft_version', None)
        self.check_defaults('server_software', None)
        for i in self.results["plugins_altver"]:
            self.results["classified_errors"][i] = []
        for i in self.results["plugins_altver"]:
            for x in self.results["errors"]:
                if i in x:
                    self.results["classified_errors"][i].append(x)
                else:
                    self.results["common_errors"].append(x)
        for key, value in self.results["classified_errors"].items():
            if not value:
                self.results["classified_errors"][key] = None
        self.check_none('common_errors')
        return self.results

    def check_defaults_bool(self, value):
        try:
            if self.results[value] is True:
                pass
        except KeyError:
            self.results[value] = False

    def check_none(self, value):
        if not self.results[value]:
            pass
        else:
            self.results[value] = None

    def check_defaults(self, value, defaults):
        try:
            if self.results[value] is not None:
                pass
        except KeyError:
            self.results[value] = defaults
