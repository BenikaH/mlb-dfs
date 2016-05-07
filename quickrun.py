#!/usr/local/bin/python2.7
import pinnaclemlb
import starting_lineups
import get_outputs

def main():

    pinnaclemlb.main()
    starting_lineups.main()
    get_outputs.main('(Early)')

    return

if __name__ == '__main__':
    main()