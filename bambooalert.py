# Dependencies: python-dateutil
# Activate a dome light every time a build is pushed to CI
# Queries Bamboo every five seconds. If the buildCompletedTime is higher than the last time, activate a GPIO
# which controls the dome light. Turn off the pin after five seconds.
from dateutil import parser
import json
import urllib.request
import sched, time


# query Bamboo to see if a new build has been pushed
# if so, activate the dome light
def check_for_new_builds():
    global lastBuildTime
    currentBuildTime = get_latest_build_time()
    if currentBuildTime > lastBuildTime:
        lastBuildTime = currentBuildTime
        print("New build detected at: ", currentBuildTime, "Activating dome light!")
        # TODO: activate dome light lol
    s.enter(5, 1, check_for_new_builds)


# retrieves the latest build time from Bamboo
# returns the value as a datetime
# https://developer.atlassian.com/display/BAMBOODEV/Bamboo+REST+Resources#BambooRESTResources-BuildService—SpecificBuildResult
def get_latest_build_time():
    url = "http://bamboo.cwmn.us/rest/api/latest/result/CWMN-SOCKET/latest.json"
    response = urllib.request.urlopen(url)
    data = response.read().decode("utf-8")
    dataJson = json.loads(data)
    # example date format from Bamboo: 2015-02-14T16:32:32.000Z
    return parser.parse(dataJson["buildCompletedTime"])


# get a baseline build time; any builds after this time will trigger the light
lastBuildTime = get_latest_build_time()

print("BambooAlert started at", time.time(), "last detected CI push", lastBuildTime)

# check for new builds every five seconds
s = sched.scheduler(time.time, time.sleep)
s.enter(5, 1, check_for_new_builds)
s.run()




