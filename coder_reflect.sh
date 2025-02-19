prompt="$1"

# first shot
aider \
    --model gpt-4o \
    --architect \
    --editor-model sonnet \
    --no-detect-urls \
    --no-auto-commit \
    --yes-always \
    --file *.py \
    --message "$prompt"

# reflection second shot
aider \
    --model gpt-4o \
    --architect \
    --editor-model sonnet \
    --no-detect-urls \
    --no-auto-commit \
    --yes-always \
    --file *.py \
    --message "Double all changes requested to make sure they've been implemented: $prompt"