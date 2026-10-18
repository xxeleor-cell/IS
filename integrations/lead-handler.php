<?php
/**
 * Пример приёма заявок с сайта (PHP 7.4+). Разместите как /api/lead.php
 * и включите в content/site.json:  "leads": { "transport": "http", "endpoint": "/api/lead.php" }
 *
 * Отправляет заявку в Telegram и/или на почту. Токены храните в файле
 * ВНЕ папки сайта: файл lead-config.php на уровень выше корня сайта
 * (путь задан в $cfgPath ниже), например:
 *
 *   <?php return [
 *     'telegram_token'   => '123:ABC',      // токен бота
 *     'telegram_chat_id' => '-100123456',   // чат, куда бот пишет заявки
 *     'mail_to'          => '',             // почта для копии заявок (необязательно)
 *   ];
 *
 * Отвечает {"ok": true} только если заявка действительно доставлена
 * хотя бы в один канал — иначе сайт покажет посетителю ошибку и контакты.
 */
header('Content-Type: application/json; charset=utf-8');

function reply(int $code, array $body) { http_response_code($code); echo json_encode($body, JSON_UNESCAPED_UNICODE); exit; }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') reply(405, ['ok' => false, 'error' => 'method']);

$cfgPath = __DIR__ . '/../../lead-config.php';
$cfg = is_file($cfgPath) ? require $cfgPath : [];

$raw = file_get_contents('php://input', false, null, 0, 64 * 1024);
$d = json_decode($raw, true);
if (!is_array($d)) reply(400, ['ok' => false, 'error' => 'bad_json']);

$s = fn($v, $max = 500) => mb_substr(trim(strip_tags((string)($v ?? ''))), 0, $max);
$name = $s($d['name'] ?? '', 80);
$phone = $s($d['phone'] ?? '', 40);
if ($name === '' || strlen(preg_replace('/\D/', '', $phone)) < 10) reply(422, ['ok' => false, 'error' => 'validation']);

// Простейшая защита от частых повторов с одного IP: не чаще раза в 20 секунд
$lock = sys_get_temp_dir() . '/lead_' . md5($_SERVER['REMOTE_ADDR'] ?? '') ;
if (is_file($lock) && time() - filemtime($lock) < 20) reply(429, ['ok' => false, 'error' => 'too_many']);
touch($lock);

$lines = [
  'Новая заявка с сайта',
  "Имя: $name",
  "Телефон: $phone",
];
foreach (['buildingType' => 'Тип строения', 'technology' => 'Технология'] as $k => $label) {
  if (!empty($d[$k]['label'])) $lines[] = "$label: " . $s($d[$k]['label'], 100);
}
if (!empty($d['project'])) $lines[] = 'Проект: ' . $s($d['project'], 200);
if (!empty($d['message'])) $lines[] = 'Пожелания: ' . $s($d['message'], 2000);
if (!empty($d['calculator']['summaryText'])) $lines[] = "\nПараметры из калькулятора:\n" . $s($d['calculator']['summaryText'], 3000);
if (!empty($d['page'])) $lines[] = "\nСтраница: " . $s($d['page'], 200);
if (!empty($d['utm']) && is_array($d['utm'])) {
  $lines[] = 'UTM: ' . $s(implode(', ', array_map(fn($k, $v) => "$k=$v", array_keys($d['utm']), $d['utm'])), 500);
}
$text = implode("\n", $lines);

$delivered = false;

if (!empty($cfg['telegram_token']) && !empty($cfg['telegram_chat_id'])) {
  $ctx = stream_context_create(['http' => [
    'method' => 'POST', 'timeout' => 8, 'ignore_errors' => true,
    'header' => "Content-Type: application/json\r\n",
    'content' => json_encode(['chat_id' => $cfg['telegram_chat_id'], 'text' => $text], JSON_UNESCAPED_UNICODE),
  ]]);
  $res = @file_get_contents('https://api.telegram.org/bot' . $cfg['telegram_token'] . '/sendMessage', false, $ctx);
  $delivered = $delivered || (is_string($res) && (json_decode($res, true)['ok'] ?? false));
}

if (!empty($cfg['mail_to'])) {
  $subject = '=?UTF-8?B?' . base64_encode('Заявка с сайта: ' . $name) . '?=';
  $delivered = mail($cfg['mail_to'], $subject, $text, "Content-Type: text/plain; charset=utf-8") || $delivered;
}

$delivered ? reply(200, ['ok' => true]) : reply(502, ['ok' => false, 'error' => 'not_delivered']);
