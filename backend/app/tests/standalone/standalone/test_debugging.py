import pytest
import sys
from enum import Enum

"""
Debugging test to check enum behavior issues.
"""


class ComparisonOperator(str, Enum):
    """Comparison operators for rule conditions."""
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"


    @pytest.mark.standalone()
    def test_enum_behavior():
        """Test the behavior of Enum classes."""
        print("\nDEBUG: Testing enum behavior")
    
        # 1. Create an enum instance
        op1 = ComparisonOperator.GREATER_THAN_OR_EQUAL
        op2 = ComparisonOperator.GREATER_THAN_OR_EQUAL
    
        # 2. Print the instance, its type, and its value
        print(f"op1: {op1}, type: {type(op1)}, value: {op1.value}")
        print(f"op2: {op2}, type: {type(op2)}, value: {op2.value}")
    
        # 3. Check if the instances are equal
        print(f"op1 == op2: {op1 == op2}")
        print(f"op1 is op2: {op1 is op2}")
    
        # 4. Create another instance with the same value
        op3 = ComparisonOperator("greater_than_or_equal")
        print(f"op3: {op3}, type: {type(op3)}, value: {op3.value}")
        print(f"op1 == op3: {op1 == op3}")
        print(f"op1 is op3: {op1 is op3}")
    
        # 5. Check comparison with string
        print(f"op1 == 'greater_than_or_equal': {op1 == 'greater_than_or_equal'}")
        print(f"op1.value == 'greater_than_or_equal': {op1.value == 'greater_than_or_equal'}")
    
        # 6. Force the test to pass or fail based on expected behavior
        assert op1  ==  op2
        assert op1  ==  op3
        assert op1  ==  "greater_than_or_equal"  # This is key!


        def simulate_rule_evaluation():
        """Simulate the rule evaluation with the enum."""
        print("\nDEBUG: Simulating rule evaluation")
    
        # Mimic the rule and data point
        operator = ComparisonOperator.GREATER_THAN_OR_EQUAL
        threshold = 100
        value = 100
    
        # Check different ways of comparing
        print(f"Method 1 (direct ==): {operator == ComparisonOperator.GREATER_THAN_OR_EQUAL}")
        print(f"Method 2 (is): {operator is ComparisonOperator.GREATER_THAN_OR_EQUAL}")
        print(f"Method 3 (value comparison): {operator.value == ComparisonOperator.GREATER_THAN_OR_EQUAL.value}")
    
        # Test the actual comparison logic
        print("\nTesting comparison logic:")
        if operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
        result = value >= threshold
        print(f"Using direct enum comparison: {result} ({value} >= {threshold})")
        else:
        print("Direct enum comparison FAILED")
    
        if operator.value == ComparisonOperator.GREATER_THAN_OR_EQUAL.value:
        result = value >= threshold
        print(f"Using value comparison: {result} ({value} >= {threshold})")
        else:
        print("Value comparison FAILED")
    
        # Return the actual result we want
        #     return value >= threshold # FIXME: return outside function


        if __name__ == "__main__":
    print("\n=== Enum Behavior Debug ===")
    test_enum_behavior()
    
    print("\n=== Rule Evaluation Simulation ===")
    result = simulate_rule_evaluation()
    print(f"\nFinal result: {result}")
    
    print("\nAll debug tests passed!")
    sys.exit(0)