import os
from flask import Flask, request, jsonify
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_shipping_cost(location_level):
    """
    Calculate shipping cost based on volumetric weight.
    """
    # Predefined package dimensions and weight
    length = 2.0  # Length in cm
    breadth = 2.0  # Width in cm
    height = 3.0  # Height in cm
    actual_weight = 10.0  # Weight in kg

    # Volumetric weight calculation
    volumetric_weight = (length * breadth * height) / 5000  # Dimensional divisor (5000) is standard in many shipping models

    # Use the higher of actual weight or volumetric weight
    chargeable_weight = max(actual_weight, volumetric_weight)

    # Determine which weight is being used
    weight_used = {
        "type": "volumetric_weight" if chargeable_weight == volumetric_weight else "actual_weight",
        "value": chargeable_weight
    }

    # Shipping rates per kg for different levels for different companies
    companies = {
        'Delhivery': {'district': 50, 'state': 60, 'national': 125},
        'DTDC': {'district': 45, 'state': 85, 'national': 120},
        'eKart': {'district': 55, 'state': 65, 'national': 130}
    }

    # Validate location level
    if location_level not in ['district', 'state', 'national']:
        raise ValueError("Invalid location level. Choose from 'district', 'state', 'national'.")

    # Calculate costs for each company
    costs = {}
    for company, rates in companies.items():
        costs[company] = chargeable_weight * rates[location_level]

    return {company: round(cost, 2) for company, cost in costs.items()}, weight_used

def determine_location_level(pincode):
    """
    Determine the location level based on the pincode.
    """
    if len(pincode) == 6 and pincode.isdigit():
        if pincode[:6] == "400001":  # Example district-level pincode
            return 'district'
        elif pincode[:2] in ["40", "41", "43", "44", "42"]:  # Example state-level pincodes
            return 'state'
        else:
            return 'national'
    else:
        raise ValueError("Invalid pincode format. Must be a 6-digit number.")

# Flask route to handle the payload
@app.route('/calculate_shipping', methods=['POST'])
def calculate_shipping():
    try:
        # Get JSON data from the request
        data = request.get_json()
        print(f"Received data: {data}")  # Debugging line

        # Extract pincode from the payload
        pincode = data.get('pincode')
        print(f"Extracted pincode: {pincode}")  # Debugging line

        # Validate that pincode is provided
        if not pincode:
            return jsonify({"error": "Missing pincode"}), 400

        # Determine location level based on pincode
        location_level = determine_location_level(pincode)

        # Calculate shipping costs using predefined values
        costs, weight_used = calculate_shipping_cost(location_level)

        # Find the company with the lowest cost
        lowest_company = min(costs, key=costs.get)
        lowest_cost = costs[lowest_company]

        # Return the result as JSON
        return jsonify({
            "shipping_costs": costs,
            "lowest_cost": {
                "company": lowest_company,
                "cost": lowest_cost,
                "location_level": location_level
            },
            "weight_used": weight_used
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=20003)