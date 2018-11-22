<?php
$SESSION_DIRECTORY = "/var/lib/apache2/session";
$SCRIPT_NAME = '/hallinta';

function login_form() {
  global $SCRIPT_NAME;
  // Read user session
  $user_info = user_data();
  if (isset($user_info['username'])) {
    ?>
      <p class="user"><?=$user_info['fullname']?><br>
      <a href="<?=$SCRIPT_NAME?>/logout">kirjaudu ulos</a></p>
    <?php
  } else {
    ?>
      <form id="login" action="<?=$SCRIPT_NAME?>/login" method="post" enctype="multipart/form-data">
        <p>Kirjaudu sisään</p>
        <input type="hidden" name="_form" value="login">
        <p>Käyttäjänimi<input type="text" name="username" value=""></p>
        <p>Salasana<input type="password" name="password" value=""></p>
        <input type="hidden" name="_next" value="<?=$_SERVER['PHP_SELF']?>">
        <input id="send" class="button" type="submit" value="Kirjaudu"><br>
      </form>
    <?php
  }
}

function user_data() {
  global $SESSION_DIRECTORY;
  // Return empty if session id does not exist
  if (!isset($_COOKIE['sessid'])) return array('_error' => 'No session id');
  $ffn = $SESSION_DIRECTORY . '/' . $_COOKIE['sessid'] . '.json';
  $json = file_get_contents($ffn);
  // Return empty if file content is empty or does not exist
  if (!$json) return array('_error' => 'Session file ' . $ffn . ' does not exist');
  $session = json_decode($json, true);
  // Return empty if session data is empty, false or nonexistent
  if (!$session) return array('_error' => 'No session data');
  // Return session data if it exists
  return $session;
}
?>
