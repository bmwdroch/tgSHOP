#!/bin/bash

# Обновляем пакеты
apt update && apt upgrade -y

# Устанавливаем необходимые зависимости
apt install -y python3.10-venv tmux

# Создаем новую tmux сессию
tmux new -s shopSession -d

# Внутри tmux сессии выполняем дальнейшие шаги
tmux send-keys "python3 -m venv virtualEnv" Enter
tmux send-keys "source virtualEnv/bin/activate" Enter
tmux send-keys "git clone https://github.com/bmwdroch/tgSHOP.git" Enter
tmux send-keys "cd tgSHOP" Enter
tmux send-keys "pip install -r requirements.txt" Enter
tmux send-keys "python main.py" Enter

echo "Установка завершена. Подключись к сессии tmux командой 'tmux attach -t shopSession' и введи токен бота и свой ID. Далее можно закрыть tmux с помощью Ctrl + B, затем отпусти и нажми D. Это отключит тебя от сессии, оставив её работающей в фоновом режиме."
