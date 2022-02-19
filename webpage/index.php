<?php
/**
 * Load confidential information from variables file like .env,
 * storing mysql connection sensitive information in public codebase is not
 * recommended.
 */
require_once('DotEnv.php');
(new DevCoder\DotEnv(__DIR__ . '/.env'))->load();

$username = filter_input(INPUT_POST, 'username');
$password = filter_input(INPUT_POST, 'password');
if (!empty($username)){
if (!empty($password)){
$host = getenv('DB_HOST');
$dbusername = getenv('DB_USERNAME');
$dbpassword = getenv('DB_PASSWORD');
$dbname = getenv('DB_NAME');
$conn = new mysqli ($host, $dbusername, $dbpassword, $dbname);

if (mysqli_connect_error()){
die('Connect Error ('. mysqli_connect_errno() .') '
. mysqli_connect_error());
}
else{
$sql = "INSERT INTO register (username, password)
values ('$username','$password')";
if ($conn->query($sql)){
echo "New record is inserted sucessfully";
}
else{
echo "Error: ". $sql ."
". $conn->error;
}
$conn->close();
}
}
else{
echo "Password should not be empty";
die();
}
}
else{
echo "Username should not be empty";
die();
}
?>
