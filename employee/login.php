<?php include 'db.php'; session_start(); ?>

<!DOCTYPE html>
<html>
<head>
  <title>Employee Login</title>
</head>
 <link rel="stylesheet" href="style.css">
<body>
  <h2>Login</h2>
  <form method="POST">
    <input type="email" name="email" placeholder="Email" required><br><br>
    <input type="password" name="password" placeholder="Password" required><br><br>
    <button type="submit" name="login">Login</button>
  </form>

<?php
if (isset($_POST['login'])) {
    $email = $_POST['email'];
    $password = $_POST['password'];

    $sql = "SELECT * FROM employees WHERE email='$email'";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        $user = $result->fetch_assoc();
        if (password_verify($password, $user['password'])) {
            $_SESSION['employee_id'] = $user['id'];
            $_SESSION['employee_name'] = $user['name'];
            header("Location: dashboard.php");
        } else {
            echo "Invalid password!";
        }
    } else {
        echo "No user found!";
    }
}
?>
</body>
</html>
