echo $COMMIT_MESSAGE
echo $TRAVIS
echo $TRAVIS_PULL_REQUEST

if [ -z "$TRAVIS_PULL_REQUEST" ]; then echo "A"; fi
if [ -n "$TRAVIS_PULL_REQUEST" ]; then echo "B"; fi
if [ ! -z "$TRAVIS_PULL_REQUEST" ]; then echo "C"; fi

if [ "$TRAVIS" = true ] && [ -z "$TRAVIS_PULL_REQUEST" ]; then
    echo "SKIPPED: Commit message check skipped!"
fi
