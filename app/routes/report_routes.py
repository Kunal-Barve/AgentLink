@app.route('/generate_agents_report', methods=['POST'])
async def generate_agents_report():
    data = request.json
    suburb = data.get('suburb', 'Queenscliff')  # Default to Queenscliff if not provided
    state = data.get('state', 'NSW')  # Default to NSW if not provided
    
    # Fetch top agents data
    agents_data = await domain_service.fetch_property_data(
        property_id=None,  # Not needed for agents report
        suburb=suburb,
        state=state
    )
    
    # Render the template with the agents data and suburb
    rendered_html = render_template(
        'agents_report.html',
        agents=agents_data['top_agents'],
        suburb=suburb  # Pass the suburb to the template
    )
    
    # Generate PDF from the rendered HTML
    # ... rest of your PDF generation code ...
    
    return jsonify({"status": "success", "message": "Agents report generated successfully"})