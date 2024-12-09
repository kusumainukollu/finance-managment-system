<script>
    var userBudgets = {{ user_budgets | tojson }};  // Dynamically set from backend
    var totalBudget = parseFloat(userBudgets.food) + parseFloat(userBudgets.transport) + parseFloat(userBudgets.entertainment) + parseFloat(userBudgets.bills) + parseFloat(userBudgets.other);
    var monthlySalary = parseFloat("{{ session['monthly_salary'] }}");

    // Check if total budget exceeds salary
    if (totalBudget > monthlySalary) {
        document.getElementById('budget-notification').style.display = 'block';
    }
</script>
