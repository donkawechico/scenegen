#!/usr/bin/python3

import requests
import argparse
import configparser
import sys

light_color_types = ["xy_color", "rgb_color", "color_temp", "color_name"]

def error(message):
    sys.stderr.write("error: %s\n" % message)
    sys.exit(1)

def get_states(url, key):
  if key != None:
    headers = {'x-ha-access': key}
  else:
    headers = {}

  apiurl = url + "/api/states"

  r = requests.get(apiurl, headers=headers)

  if r.status_code != 200:
    error("Error calling Home Assistant: {}, {}".format(r.status_code, r.reason))

  return r.json()

def output_attrs(state, args):
  parts = state["entity_id"].split(".")
  type = parts[0]
  name = parts[1]
  light_attrs = ["transition", "profile", "brightness", "flash"]
  light_color_types = ["xy_color", "rgb_color", "color_temp", "color_name"]
  if type == "light" and "light" in args.types:
    print ("  {}:".format(state["entity_id"]))
    print ("    state: {}".format(state["state"]))
    for attr in light_attrs:
      if attr in state["attributes"]:
          print("    {}: {}".format(attr, round(float(state["attributes"][attr]))))
    for color_type in light_color_types:
      if color_type in state["attributes"] and args.colortype == color_type:
        print("    {}: {}".format(color_type, state["attributes"][color_type]))
  if type == "switch" and "switch" in args.types:
    print ("  {}:".format(state["entity_id"]))
    print ("    state: {}".format(state["state"]))

def main():
  # Get command line args

  parser = argparse.ArgumentParser()

  parser.add_argument("-u", "--url", help="url for Home Assistant instance")
  parser.add_argument("-k", "--key", help="API Key of Home Assistant instance")
  parser.add_argument("-s", "--scenename", help="Name of scene to generate", default = "My New Scene")
  parser.add_argument("-m", "--mapfile", help="Name of mapfile to enable device filtering")
  parser.add_argument("-e", "--secrets", help="Name of secrets config to hide sensitive data")
  parser.add_argument("-f", "--filter", help="Comma separated list of device collections as defined in mapfile")
  parser.add_argument("-c", "--colortype", help="color type to use", default = "color_temp", choices = light_color_types)
  parser.add_argument("-t", "--types", help="list of device types to include", default = "light,switch")
  args = parser.parse_args()

  if args.url is None and args.secrets is None:
    error("You must specify either a url or secrets file")

  devices = {}
  config = configparser.ConfigParser()
  if args.mapfile:
    config.read_file(open(args.mapfile))
    for section in config.sections():
      devices[section] = {}
      for option in config.options(section):
        devices[section][option] = config.get(section, option)

  filters = []
  if args.filter:
    if args.mapfile:
      filters = args.filter.split(",")
    else:
      error("Must specify a mapfile if using filters")

  try:
    if args.secrets:
      config.read_file(open(args.secrets))
      args.key = config.get("HA","api_key")
      args.url = config.get("HA","ha_url")

    states = get_states(args.url, args.key)
    print("name: {}".format(args.scenename))
    print("entities:")
    for state in states:
      if args.mapfile:
        if args.filter:
          for filter in filters:
            if filter in devices and state["entity_id"] in devices[filter]:
              output_attrs(state, args)
        else:
          for section in devices:
            if state["entity_id"] in devices[section]:
              output_attrs(state, args)
      else:
        output_attrs(state, args)

  except:
    raise

if __name__ == "__main__":
    main()
