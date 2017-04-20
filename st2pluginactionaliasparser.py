# coding:utf-8
import re
import sys
import copy
import logging

LOG = logging.getLogger(__name__)


class St2PluginActionAliasParser(object):
    """
    A class to process Action Aliases to be made available through errbot.
    """
    def __init__(self, bot_prefix=""):
        self.pattern_action = {}
        self.help = ''
        self.bot_prefix = bot_prefix

    def show_help(self):
        """
        Return help information for action aliases for errbot to display.
        """
        return self.help

    def process_actionaliases(self, action_aliases):
        """
        Fetch the list of action aliases from st2 and refresh the internal list of patterns.
        """
        self.help = ''
        self.pattern_action = {}

        for action_alias in action_aliases:

            if not action_alias.enabled:
                continue

            for _format in action_alias.formats:

                try:
                    display, representations = self._normalise_format(_format)
                except Exception as e:
                    # Skip malformed formats and move on to the next
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    LOG.warn("Unable to process actionalias = Exception [%s:%s]: %s" % (type(e),
                                                                                        e,
                                                                                        _format))
                    continue

                # Include formats which contain only a help strings.
                if display and len(representations) == 0:
                    self.help += '{}{} -- {}\r\n'.format(self.bot_prefix,
                                                         display,
                                                         action_alias.description)

                for representation in representations:
                    if not (isinstance(representation, str) or isinstance(representation, unicode)):
                        LOG.info("Skipping: %s which is type %s" % (action_alias.action_ref,
                                                                    type(representation)))
                        continue

                    pattern_context, kwargs = self._format_to_pattern(representation)

                    self.pattern_action[pattern_context] = {
                        "action_ref": action_alias.action_ref,
                        "kwargs": kwargs
                    }

                    self.help += '{}{} -- {}\r\n'.format(self.bot_prefix,
                                                         display,
                                                         action_alias.description)

        if self.help == '':
            self.help = 'No Action-Alias definitions were found.  No help is available.'

    def _normalise_format(self, alias_format):
        """
        Stackstorm action aliases can have two types;
            1. A simple string holding the format
            2. A dictionary which holds numberous alias format "representation(s)"
               With a single "display" for help about the action alias.
        This function processes both forms and returns a standardised form.
        """
        display = None
        representation = []
        if isinstance(alias_format, str) or isinstance(alias_format, bytes):
            display = alias_format
            representation.append(alias_format)
        if isinstance(alias_format, dict):
            display = alias_format.get('display')
            representation = alias_format.get('representation') or []
        return (display, representation)

    def _format_to_pattern(self, alias_format):
        """
        Extract named arguments from format to create a keyword argument list.
        Transform tokens into regular expressions.
        """
        kwargs = {}
        # Step 1: Extract action alias arguments so they can be used later
        #         when calling the stackstorm action.
        tokens = re.findall(r"{{(.*?)}}", alias_format, re.IGNORECASE)
        for token in tokens:
            name = val = None
            for i, v in enumerate(token.split("=", 1)):
                v = v.strip()
                if i:
                    val = v
                else:
                    name = v
            kwargs[name] = val
            name = r"?P<{}>[\s\S]+?".format(name)

            # The below code causes a regex exception to be raised under certain conditions.
            # Using replace() as alternative.
            # alias_format = re.sub( r"\s*{{{{{}}}}}\s*".format(token),
            #                           r"\\s*({})\\s*".format(name), alias_format)
            # Replace token with named group match.
            alias_format = alias_format.replace(r"{{{{{}}}}}".format(token), r"({})".format(name))

        # Step 2: Append regex to match any extra parameters that
        #         weren't declared in the action alias.
        extra_params = r"""(:?\s+(\S+)\s*=("([\s\S]*?)"|'([\s\S]*?)'|({[\s\S]*?})|(\S+))\s*)*"""
        alias_format = r'^{}{}{}$'.format(self.bot_prefix, alias_format, extra_params)

        return (re.compile(alias_format, re.I), kwargs)

    def _extract_extra_params(self, extra_params):
        """
        Returns a dictionary of extra parameters supplied in the action_alias.
        """
        kwargs = {}
        for arg in extra_params.groups():
            if arg and "=" in arg:
                k, v = arg.split("=", 1)
                kwargs[k.strip()] = v.strip()
        return kwargs

    def match(self, text):
        """
        Match the text against an action and return the action reference.
        """
        results = []
        for pattern in self.pattern_action:
            res = pattern.search(text)
            if res:
                data = {}
                # Create keyword arguments starting with the defaults.
                # Deep copy is used here to avoid exposing the reference
                # outside the match function.
                data.update(copy.deepcopy(self.pattern_action[pattern]))
                # Merge in the named arguments.
                data["kwargs"].update(res.groupdict())
                # Merge in any extra arguments supplied as a key/value pair.
                data["kwargs"].update(self._extract_extra_params(res))
                results.append(data)

        if not results:
            return None

        if len(results) > 1:
            LOG.warn("Matched more the one alias pattern. %s" % (results))
        results.sort(reverse=True)
        return results[0]
