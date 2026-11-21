trap 'exit 1' ERR

#
# PRECONDITION: inherited env vars MUST include:
#      DJANGO_APP: django application directory name
#
# OPTIONAL: mount a directory at /coverage to collect coverage results

# start virtualenv
source bin/activate

# Write coverage directly to the mounted directory when available.
if [ -d /coverage ]; then
    export COVERAGE_FILE=/coverage/.coverage
fi

function run_test {
    echo "##########################"
    echo "TEST: $1"
    eval $1
}

if [ -d ${DJANGO_APP}/static/${DJANGO_APP}/js ]; then
    run_test "jshint ${DJANGO_APP}/static/${DJANGO_APP}/js --verbose"
elif [ -d ${DJANGO_APP}/static/js ]; then
    run_test "jshint ${DJANGO_APP}/static/js --verbose"
fi

run_test "python -Wd -m coverage run --parallel-mode --source=${DJANGO_APP} '--omit=*/migrations/*,*/tests/*' manage.py test ${DJANGO_APP} --settings=project.test_settings"

exit 0
