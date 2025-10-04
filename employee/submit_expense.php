<?php 
include 'db.php';
session_start();
if(!isset($_SESSION['employee_id'])) { header("Location: login.php"); exit; }
?>

<!DOCTYPE html>
<html>
<head><title>Submit Expense</title></head>
<body>
<h2>Submit Expense</h2>
<form method="POST">
  Amount: <input type="number" step="0.01" name="amount" required><br><br>
  Currency: <input type="text" name="currency" placeholder="e.g. USD" required><br><br>
  Category: 
  <select name="category" required>
    <option value="Travel">Travel</option>
    <option value="Food">Food</option>
    <option value="Accommodation">Accommodation</option>
    <option value="Other">Other</option>
  </select><br><br>
  Description: <textarea name="description" required></textarea><br><br>
  Date: <input type="date" name="expense_date" required><br><br>
  <button type="submit" name="submit_expense">Submit</button>
</form>

<?php
if (isset($_POST['submit_expense'])) {
    $employee_id = $_SESSION['employee_id'];
    $amount = $_POST['amount'];
    $currency = $_POST['currency'];
    $category = $_POST['category'];
    $description = $_POST['description'];
    $expense_date = $_POST['expense_date'];

    $sql = "INSERT INTO expenses (employee_id, amount, currency, category, description, expense_date) 
            VALUES ('$employee_id', '$amount', '$currency', '$category', '$description', '$expense_date')";
    if ($conn->query($sql)) {
        echo "Expense submitted successfully!";
    } else {
        echo "Error: " . $conn->error;
    }
}
?>
</body>
</html>
