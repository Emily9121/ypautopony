if __name__ != '__main__':
    raise 'huh? this is not a module...'

import sys, os, glob, subprocess
try:
    import tvdb.tvdb_api
    tvdb = tvdb.tvdb_api.Tvdb()
except:
    print >> sys.stderr, 'Error importing tvdb_api!'

# ok this is real simple..
paths = { }
options = { }
dynamic = { }
commands = { }

# open the file
with open("config") as f:

    # go line by line
    for line in f:

        # strip off any kind of comment
        line = line.split('#', 1)[0]
        # strip off whitespace
        line = line.strip()
        # ignore empty lines
        if len(line) == 0:
            continue

        # are we there yet?
        if line == 'COMMANDS':
            # done with settings! onwards!
            break

        # this should be an option line. split off args
        line = line.split(None, 1)

        if len(line) != 2:
            print >> sys.stderr, 'Error: Missing attribute for', line[0]
            sys.exit(1)

        # dir arguments, save those (and make sure they are dirs)
        if line[0][0:3] == 'DIR':
            if not os.path.isdir(line[1]):
                print >> sys.stderr, 'Error: Path for', line[0], 'wrong or does not exist:', line[1]
                sys.exit(1)

            # alright, just note this down for later
            paths[line[0]] = line[1]

        # dir arguments, save those (and make sure they are paths)
        if line[0][0:3] == 'PATH_':
            if not os.path.exists(line[1]):
                print >> sys.stderr, 'Error: Path for', line[0], 'wrong or does not exist:', line[1]
                sys.exit(1)

            # alright, just note this down for later
            paths[line[0]] = line[1]

        # dynamic arguments
        if line[0][0] == '?':

            # alright, just note this down for later
            dynamic[line[0][1:]] = line[1]

        # the one season argument - we need this one for tvdb!
        elif line[0] == 'SEASON':
            try:
                options['SEASON'] = int(line[1])
            except:
                print >> sys.stderr, 'Error: SEASON should be a number!'
                sys.exit(1)

        # it's a command
        elif line[0] == 'CMD':
            cmd = ''
            for line2 in f:
                # strip off any kind of comment
                line2 = line2.split('#', 1)[0]
                # strip off whitespace
                line2 = line2.strip()
                # ignore empty lines
                if len(line2) == 0:
                    break

                cmd += line2 + ' '

            commands[line[1]] = cmd

        # just note down everything else
        else:
            options[line[0]] = line[1]

    # print commands

    # make sure all dynamic options are valid!
    for key in dynamic:
        if key + "_0" not in options:
            print >> sys.stderr, "Missing", key + "_0 for dynamic value!"
            sys.exit(8)
        if key + "_1" not in options:
            print >> sys.stderr, "Missing", key + "_1 for dynamic value!"
            sys.exit(8)

    # all settings done, we are getting the file names from here on out!
    files = set()

    # again, go line by line
    for line in f:

        # strip off any kind of comment
        line = line.split('#', 1)[0]
        # strip off whitespace
        line = line.strip()
        # ignore empty lines
        if len(line) == 0:
            continue

        line = line.split(None, 1)

        # not a valid command? probably a typo...
        if line[0] not in commands:
            print >> sys.stderr, 'Error: Invalid command', line[0]
            sys.exit(6)

        # glob the supplied filename
        fpaths = glob.glob(paths['DIR_IN_' + line[0]] + os.path.sep + line[1])
        if len(fpaths) == 0:
            print >> sys.stderr, 'Error: Unable to find file or invalid glob:', line
            sys.exit(2)
        elif len(fpaths) > 1:
            if 'ALLOW_MULTIPLE' in options and options['ALLOW_MULTIPLE'] not in [ 'yes', '1', 'true' ]:
                print 'Error: Expression', line[1], 'matched', len(fpaths), 'files'
                sys.exit(7)

        for fpath in fpaths:

            # ok, that should be all. prepare variables
            fname = os.path.basename(fpath)
            try:
                epnum = int(fname.split(None, 1)[0])
            except:
                print >> sys.stderr, 'Error: Could not find episode number for', fname
                sys.exit(4)

            # fetch a proper episode name from thetvdb
            episode = tvdb['My Little Pony: Friendship Is Magic'][options['SEASON']][epnum]
            epname = episode['episodename']

            # set up the variable dict
            variables = paths
            variables.update(options)

            if dynamic:
                print "For {}:".format(fname)
                for key in dynamic:
                    if raw_input("- {} ".format(dynamic[key])) in [ 'y', 'yes', '1', 'true' ]:
                        variables[key] = options[key + '_1']
                    else:
                        variables[key] = options[key + '_0']


            variables.update({
                    '_FILE': fpath,
                    '_FILE_NAME': fname,
                    '_EPNUM': epnum,
                    '_EPNAME': epname,
                })

            cmd = commands[line[0]].format(**paths)

            print
            # apply formatting to command string
            print cmd

            if 'DRY_RUN' in options and options['DRY_RUN'] in [ 'yes', '1', 'true' ]:
                print 'DRY_RUN enabled, skipping command..'
                continue

            if 'ASK_BEFORE' in options and options['ASK_BEFORE'] in [ 'yes', '1', 'true' ]:
                if raw_input('Execute this? (y to confirm) ') != 'y':
                    print 'Skipping command..'
                    continue

            print 'Running..'
            sts = subprocess.call(cmd, shell=True)
            if sts != 0:
                print >> sys.stderr, 'Skipping command..'

            # just printing, no execution at the moment

