#!/usr/bin/env python
import cmd
import json
import optparse
import pydoc
import sys
import os
import logging

from pydiscourse.client import DiscourseClient, DiscourseError


class DiscourseCmd(cmd.Cmd):
    prompt = 'discourse>'
    output = sys.stdout

    def __init__(self, client):
        cmd.Cmd.__init__(self)
        self.client = client
        self.prompt = '%s>' % self.client.host

    def __getattr__(self, attr):
        if attr.startswith('do_'):
            method = getattr(self.client, attr[3:])

            def wrapper(arg):
                args = arg.split()
                kwargs = dict(a.split('=') for a in args if '=' in a)
                args = [a for a in args if '=' not in a]
                try:
                    return method(*args, **kwargs)
                except DiscourseError as e:
                    print e, e.response.text
                    return e.response
            return wrapper

        elif attr.startswith('help_'):
            method = getattr(self.client, attr[5:])

            def wrapper():
                self.output.write(pydoc.render_doc(method))

            return wrapper

        raise AttributeError

    def postcmd(self, result, line):
        try:
            json.dump(result, self.output, sort_keys=True, indent=4, separators=(',', ': '))
        except TypeError:
            self.output.write(result.text)


def main():
    op = optparse.OptionParser()
    op.add_option('--host', default='http://localhost:4000')
    op.add_option('--api-user', default='system')
    op.add_option('-v', '--verbose', action='store_true')

    api_key = os.environ['DISCOURSE_API_KEY']
    options, args = op.parse_args()
    client = DiscourseClient(options.host, options.api_user, api_key)

    if options.verbose:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

    c = DiscourseCmd(client)
    if args:
        line = ' '.join(args)
        result = c.onecmd(line)
        c.postcmd(result, line)
    else:
        c.cmdloop()


if __name__ == '__main__':
    main()
