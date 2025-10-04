<?php 
session_start(); 
if(!isset($_SESSION['employee_id'])) { header("Location: login.php"); exit; }
?>

<!DOCTYPE html>
<html>
<head><title>Dashboard</title></head>
<body>
  <h2>Welcome, <?php echo $_SESSION['employee_name']; ?></h2>
  <a href="submit_expense.php">Submit Expense</a> | 
  <a href="expense_history.php">View Expense History</a> | 
  <a href="logout.php">Logout</a>
</body>
</html>
