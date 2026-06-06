# Twitch Drops Loot - Updater (Авто-обновление хэшей GQL)

Этот проект содержит автоматический скрапер GraphQL-хэшей Twitch и настроенный GitHub Actions Workflow, который сканирует клиентские скрипты Twitch, извлекает актуальные SHA-256 хэши для персистентных запросов и сохраняет их в `constants.json`.

Благодаря этому Flutter-приложение может подтягивать свежие хэши «на лету» без необходимости пересборки.

---

## Как настроить на GitHub

Чтобы запустить автоматическое обновление по расписанию:

### Шаг 1: Создание репозитория на GitHub
1. Перейдите на [github.com](https://github.com) и создайте новый публичный или приватный репозиторий (например, `twitch-drops-updater`).
2. Инициализируйте репозиторий и залейте файлы из этой папки (`twitch_drops_updater`) туда:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/ВАШ_ЛОГИН/twitch-drops-updater.git
   git push -u origin main
   ```

### Шаг 2: Включение прав на запись для GitHub Actions (ВАЖНО!)
По умолчанию GitHub Actions не имеют права делать коммиты и пушить изменения обратно в репозиторий. Чтобы скрипт мог сам коммитить обновленный `constants.json`:
1. Зайдите в ваш репозиторий на GitHub.
2. Перейдите в раздел **Settings** (Настройки) -> **Actions** -> **General** (Общие).
3. Прокрутите страницу вниз до раздела **Workflow permissions** (Права доступа воркфлоу).
4. Выберите пункт **Read and write permissions** (Разрешить чтение и запись).
5. Нажмите кнопку **Save** (Сохранить).

---

## Как это работает?

* Воркфлоу запускается **каждый день в 00:00 UTC** (вы также можете запустить его вручную в панели **Actions** -> **Update Twitch GQL Hashes** -> **Run workflow**).
* Скрипт `fetch_hashes.py` скачивает главную страницу Twitch, парсит ссылки на все JS-бандлы, скачивает их в многопоточном режиме и вытягивает актуальные хэши.
* Если хэши изменились, GitHub Actions делает автоматический коммит с сообщением `chore: auto-update twitch gql hashes [skip ci]`.
* Ссылка на ваш файл в интернете всегда будет статичной:
  `https://raw.githubusercontent.com/ВАШ_ЛОГИН/twitch-drops-updater/main/constants.json`

---

## Интеграция во Flutter-приложение

Чтобы приложение использовало динамические хэши вместо захардкоженных:

1. При запуске приложения (например, в `main.dart` или при инициализации `GqlService`):
   ```dart
   final response = await http.get(Uri.parse('https://raw.githubusercontent.com/ВАШ_ЛОГИН/twitch-drops-updater/main/constants.json'));
   if (response.statusCode == 200) {
     final Map<String, dynamic> hashes = jsonDecode(response.body);
     // Сохраните их локально (например, в Hive или SharedPreferences)
   }
   ```
2. В классе `GqlOperation` (файл `gql_operations.dart`) замените статичный `sha256Hash` на динамический поиск:
   ```dart
   // Пример
   static GqlOperation get campaigns {
     final savedHash = localSettings.getHash('ViewerDropsDashboard') ?? '5a4da2ab3d5b47c9f9ce864e727b2cb346af1e3ea8b897fe8f704a97ff017619';
     return GqlOperation(
       operationName: 'ViewerDropsDashboard',
       sha256Hash: savedHash,
       variables: {'fetchRewardCampaigns': false},
     );
   }
   ```
