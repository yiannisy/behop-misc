<html>
<head><meta http-equiv="REFRESH" content="0;url=http://www.stanford.edu/~yiannisy/cgi-bin/behop/thanks.html"></head>
<body>
<?php
$file = 'people.txt';
// The new person to add to the file
$person = $_POST["fname"];
$person_webauth = $_ENV["REMOTE_USER"];
$agree = isset($_POST["agree"]) && $_POST["agree"] == "yes";
$studio = $_POST["studio"];
$ip = $_SERVER["REMOTE_ADDR"];
$date = date("Y:m:d|H:i:s");
$log = $person . "," . $person_webauth . "," . $studio . "," . $agree . "," . $ip . "," . $date . "\n";
mail("yiannisy@stanford.edu","BeHop Sign-Up",$log,"From:behop-signup@stanford.edu");
// Write the contents to the file, 
// using the FILE_APPEND flag to append the content to the end of the file
// and the LOCK_EX flag to prevent anyone else writing to the file at the same time
file_put_contents($file, $log, FILE_APPEND | LOCK_EX);
?>
</body>
</html>
