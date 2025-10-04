<?php 
include 'db.php';
session_start();
if(!isset($_SESSION['employee_id'])) { header("Location: login.php"); exit; }
$employee_id = $_SESSION['employee_id'];
?>

<!DOCTYPE html>
<html>
<head><title>Expense History</title></head>
<body>
<h2>Your Expense History</h2>
<table border="1" cellpadding="8">
  <tr>
    <th>ID</th>
    <th>Amount</th>
    <th>Currency</th>
    <th>Category</th>
    <th>Description</th>
    <th>Date</th>
    <th>Status</th>
  </tr>

<?php
$sql = "SELECT * FROM expenses WHERE employee_id='$employee_id' ORDER BY submitted_at DESC";
$result = $conn->query($sql);
while ($row = $result->fetch_assoc()) {
  echo "<tr>
          <td>{$row['id']}</td>
          <td>{$row['amount']}</td>
          <td>{$row['currency']}</td>
          <td>{$row['category']}</td>
          <td>{$row['description']}</td>
          <td>{$row['expense_date']}</td>
          <td>{$row['status']}</td>
        </tr>";
}
?>
</table>
</body>
</html>
