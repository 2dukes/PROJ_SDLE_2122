#!/bin/bash

usage() {
  # Display the usage and exit.
  echo
  echo "Usage: ${0} [-X] [-P || -p <PUBLISHER_ID>] [-S || -s <SUBSCRIBER_ID>]" >&2
  echo 'Cleans backups for publishers, subscribers and/or proxy.' >&2
  echo "  -P                Clean backups for all publishers." >&2
  echo '  -S                Clean backups for all subscribers.' >&2
  echo '  -X                Clean backups for proxy.' >&2
  echo '  -p PUBLISHER_ID   Clean backups for a specific publisher.' >&2
  echo '  -s SUBSCRIBER_ID  Clean backups for a specific subscriber.' >&2
  exit 1
}

PUB_ALL='false'
SUB_ALL='false'
PROXY='false'

while getopts PSXp:s:h OPTION
do
  case ${OPTION} in
    p) PUB="${OPTARG}" ;;
    s) SUB="${OPTARG}" ;;
    P) PUB_ALL='true' ;;
    S) SUB_ALL='true' ;;
    X) PROXY='true' ;;
    h) usage ;;
  esac
done

# Publishers
if [[ ! -z "${PUB-}" ]] && [[ "${PUB_ALL}" = 'true' ]] # -p X && -P
then
  echo "Can't specify -p and -P at the same time!"
  usage
  exit 1
elif [[ ! -z "${PUB-}" ]] # When -p 1
then
  rm "backup/publishers/${PUB}" 2> /dev/null
elif [[ "${PUB_ALL}" = 'true' ]]
then
  rm backup/publishers/* 2> /dev/null
fi

# Subscribers
if [[ ! -z "${SUB-}" ]] && [[ "${SUB_ALL}" = 'true' ]] # -s X && -S
then
  echo "Can't specify -s and -S at the same time!"
  usage
  exit 1
elif [[ ! -z "${SUB-}" ]] # When -s 1
then
  rm "backup/subscribers/${SUB}" 2> /dev/null
elif [[ "${SUB_ALL}" = 'true' ]]
then
  rm backup/subscribers/* 2> /dev/null
fi

# Proxy
if [[ "${PROXY}" = 'true' ]]
then
  rm backup/proxy 2> /dev/null
  rm backup/proxy_tmp 2> /dev/null
fi