from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==========================================
# KNOWLEDGE BASE: VW Polo GT TSI (Early 2015)
# ==========================================
# This dictionary acts as our formal Knowledge Representation.
# Each key represents a node in the decision tree.
# 'type' determines if the Inference Engine should ask a question or output a diagnosis.

diagnostic_kb = {    "start": {"type": "question", "text": "Does the primary symptom relate to warning lights illuminating on the dashboard?", "yes": "warning_lights", "no": "drivetrain_engine"},
    "warning_lights": {"type": "question", "text": "Are multiple warning lights (specifically ABS, ESC, and TPMS) illuminated simultaneously?", "yes": "abs_sensor", "no": "check_engine"},
    "abs_sensor": {"type": "diagnosis", "text": "DIAGNOSIS: Classic VW ABS wheel speed sensor failure. When one sensor fails, the ABS, ESC, and Tire Pressure Monitoring System lose wheel speed data, triggering all three warning lights simultaneously. Scan via VCDS to isolate the faulty wheel sensor."},
    "check_engine": {"type": "question", "text": "Is the Check Engine Light (CEL) or EPC warning light currently illuminated?", "yes": "epc_heavy_load", "no": "flashing_wrench"},
    "epc_heavy_load": {"type": "question", "text": "Does the EPC light trigger specifically during heavy acceleration or high RPMs, inducing limp mode?", "yes": "diag_turbo_actuator", "no": "cel_flashing"},
    "diag_turbo_actuator": {"type": "diagnosis", "text": "DIAGNOSIS: Turbocharger Wastegate Actuator Failure or Boost Leak. The 1.2 TSI ECU detects underboost during heavy load and cuts power to protect the engine. The actuator rod may be seized or the internal wastegate flap may be worn."},
    "cel_flashing": {"type": "question", "text": "Is the Check Engine Light flashing rapidly while the engine misfires heavily or stumbles?", "yes": "diag_misfire_coil", "no": "epc_other"},
    "diag_misfire_coil": {"type": "diagnosis", "text": "DIAGNOSIS: Active cylinder misfire. A flashing CEL indicates raw fuel is reaching the catalytic converter. Immediately pull over. This is highly indicative of a failed ignition coil or spark plug on the 1.2 TSI. Scan for P0301-P0304 codes."},
    "epc_other": {"type": "question", "text": "Does the EPC light remain solid immediately upon starting the engine, regardless of load?", "yes": "diag_throttle_body", "no": "flashing_wrench"},
    "diag_throttle_body": {"type": "diagnosis", "text": "DIAGNOSIS: Throttle body alignment issue or accelerator pedal position sensor fault. Perform a Throttle Body Alignment (TBA) procedure using VCDS."},
    "flashing_wrench": {"type": "question", "text": "Is there a flashing wrench symbol appearing on the Multi-Information Display (MID) where the gear indicator usually sits?", "yes": "diag_mechatronic_accum", "no": "coolant_light"},
    "diag_mechatronic_accum": {"type": "diagnosis", "text": "DIAGNOSIS: Mechatronic Unit Hydraulic Pressure Loss. The DQ200 valve body pressure accumulator is likely failing, compromised, or leaking hydraulic fluid. This requires immediate intervention before total transmission failure."},
    "coolant_light": {"type": "question", "text": "Is the red coolant temperature warning light illuminated or flashing?", "yes": "diag_coolant_level", "no": "oil_light"},
    "diag_coolant_level": {"type": "diagnosis", "text": "DIAGNOSIS: Extreme coolant temperature or deficient coolant level. Check the G12/G13 expansion tank immediately. Do not operate the vehicle until the cooling system is verified."},
    "oil_light": {"type": "question", "text": "Is the red oil pressure warning light illuminated?", "yes": "diag_oil_pressure", "no": "other_warning_light"},
    "diag_oil_pressure": {"type": "diagnosis", "text": "DIAGNOSIS: Critical loss of engine oil pressure. Halt engine operation instantly to prevent catastrophic failure. Inspect oil level and oil pump functionality."},
    "other_warning_light": {"type": "diagnosis", "text": "DIAGNOSIS: An unclassified warning light is active. Please consult the VW Polo Owner's Manual and connect a VCDS diagnostic interface to query the specific module."},
    "drivetrain_engine": {"type": "question", "text": "Does the primary symptom relate to the transmission (shifting irregularities, jerking) or general drivetrain operation?", "yes": "trans_shudder", "no": "engine_performance"},
    "trans_shudder": {"type": "question", "text": "Are you experiencing a noticeable judder or severe shuddering sensation specifically when the gearbox shifts from D2 to D1 at low speeds?", "yes": "diag_dq200_clutch", "no": "shift_delay"},
    "diag_dq200_clutch": {"type": "diagnosis", "text": "DIAGNOSIS: DQ200 DSG Dry Clutch Pack Wear. This shuddering is a prominent characteristic of the early 2015 (Pre-Update) Polo GT TSI transmissions due to thermal degradation of the friction material. Run a basic settings clutch adaptation via VCDS or prepare for clutch replacement."},
    "shift_delay": {"type": "question", "text": "Is there a noticeable delay, hesitation, or mechanical clunk when shifting from Park (P) into Drive (D) or Reverse (R)?", "yes": "trans_clunk", "no": "gear_slip"},
    "trans_clunk": {"type": "diagnosis", "text": "DIAGNOSIS: Mechatronic actuator wear or insufficient hydraulic pressure applied to the gear selection forks. Suggest observing measuring blocks via VCDS for hydraulic pressure build times."},
    "gear_slip": {"type": "question", "text": "Does the transmission seem to slip, causing uncharacteristic RPM flaring without corresponding acceleration in either even or odd gears?", "yes": "diag_dsg_fork", "no": "trans_noise"},
    "diag_dsg_fork": {"type": "diagnosis", "text": "DIAGNOSIS: Excessive wear on one specific clutch (K1 for odd gears, K2 for even gears) or a jammed shift selector fork inside the DQ200 gearbox."},
    "trans_noise": {"type": "question", "text": "Do you hear a loud metallic rattling noise coming from the transmission area when traversing rough roads at low speeds?", "yes": "diag_dsg_rattle", "no": "other_trans"},
    "diag_dsg_rattle": {"type": "diagnosis", "text": "DIAGNOSIS: Normal DQ200 Gear Rattle. The 7-speed dry clutch DSG inherently generates mechanical chatter from unloaded gear sets during low-speed oscillation. This is considered acceptable operational noise by VW."},
    "other_trans": {"type": "diagnosis", "text": "DIAGNOSIS: Atypical transmission behavior that requires advanced diagnostic logging of the Transmission Control Module (TCM) via VCDS to accurately diagnose."},
    "engine_performance": {"type": "question", "text": "Does the primary symptom relate to engine operational feel, such as rough idling, misfiring, or hesitation?", "yes": "cold_start_misfire", "no": "engine_sound"},
    "cold_start_misfire": {"type": "question", "text": "Is the engine experiencing a rough idle, stuttering, or an uncharacteristically long crank duration specifically during cold starts?", "yes": "diag_carbon_buildup", "no": "knock_ping"},
    "diag_carbon_buildup": {"type": "diagnosis", "text": "DIAGNOSIS: Severe Carbon Buildup on Intake Valves. Because the 1.2 TSI utilizes Direct Injection, port-injected fuel does not wash the intake valves. Carbon accretion restricts airflow at idle. Walnut blasting the intake ports is highly recommended."},
    "knock_ping": {"type": "question", "text": "Are you experiencing a knocking, pinging, or pre-ignition sound under moderate to heavy engine load?", "yes": "fuel_quality", "no": "power_loss"},
    "fuel_quality": {"type": "question", "text": "Are you fueling the vehicle with standard 91 RON petrol instead of the OEM recommended 95 RON?", "yes": "diag_octane", "no": "diag_knock_sensor"},
    "diag_octane": {"type": "diagnosis", "text": "DIAGNOSIS: Suboptimal Fuel Octane. The highly-strung 1.2 TSI engine requires 95 Octane (e.g., XP95) fuel to inhibit pre-ignition. Use of 91 RON forces the ECU to harshly retard ignition timing, causing knocking and power loss."},
    "diag_knock_sensor": {"type": "diagnosis", "text": "DIAGNOSIS: Potential knock sensor malfunction or critical carbon buildup artificially raising dynamic compression ratios. Further physical inspection is required."},
    "power_loss": {"type": "question", "text": "Is there a persistent lack of peak power or general sluggishness across the turbo RPM range (2000-4000 RPM)?", "yes": "diag_diverter_valve", "no": "idle_fluctuation"},
    "diag_diverter_valve": {"type": "diagnosis", "text": "DIAGNOSIS: Turbocharger Diverter Valve (DV) failure. The internal diaphragm is likely rupturing under boost, venting pressurized air back into the intake tract and reducing volumetric efficiency."},
    "idle_fluctuation": {"type": "question", "text": "Does the RPM needle fluctuate erratically (hunting) while idling at a complete stop?", "yes": "diag_pcv", "no": "other_engine_feel"},
    "diag_pcv": {"type": "diagnosis", "text": "DIAGNOSIS: PCV (Positive Crankcase Ventilation) valve diaphragm rupture. A torn PCV introduces a significant unmetered vacuum leak, causing idle instability and potential lean condition."},
    "other_engine_feel": {"type": "diagnosis", "text": "DIAGNOSIS: Non-specific engine operational issue. Recommend logging specified vs actual boost, fuel rail pressure, and lambda values via VCDS."},
    "engine_sound": {"type": "question", "text": "Does the primary issue involve abnormal mechanical sounds or distinct fluid leaks?", "yes": "cold_start_rattle", "no": "diag_healthy"},
    "cold_start_rattle": {"type": "question", "text": "Do you hear a sharp, metallic rattling sound emanating from the engine block for exactly 2-3 seconds immediately upon a cold start?", "yes": "diag_timing_chain", "no": "coolant_loss"},
    "diag_timing_chain": {"type": "diagnosis", "text": "DIAGNOSIS: Timing chain elongation or hydraulic timing chain tensioner failure. The tensioner requires a few seconds of oil pressure on cold starts. If slack is excessive, the chain rattles against the guides. Immediate replacement is crucial to avert catastrophic valve-to-piston contact."},
    "coolant_loss": {"type": "question", "text": "Are you experiencing a slow, consistent loss of G12/G13 coolant from the reservoir without any obvious pooling under the chassis?", "yes": "diag_water_pump", "no": "oil_loss"},
    "diag_water_pump": {"type": "diagnosis", "text": "DIAGNOSIS: Water pump housing micro-fracture or weeping gasket. The 1.2 TSI water pump module is prone to thermal cycling fractures that evaporate coolant on the hot block before dripping to the floor."},
    "oil_loss": {"type": "question", "text": "Is the engine consuming excessive amounts of lubricating oil (more than 1L per 2000 km)?", "yes": "diag_piston_rings", "no": "hissing_sound"},
    "diag_piston_rings": {"type": "diagnosis", "text": "DIAGNOSIS: Early-stage piston oil control ring deterioration or substantial PCV system oil bypass. A compression test and cylinder leak-down test are strongly advised."},
    "hissing_sound": {"type": "question", "text": "Do you hear a prominent hissing or whistling sound emanating from the engine bay when accelerating under load?", "yes": "diag_boost_leak", "no": "other_sound"},
    "diag_boost_leak": {"type": "diagnosis", "text": "DIAGNOSIS: Unmetered air/boost leak in the charged air pipework. Inspect all intercooler silicone couplers, O-rings, and the charge pipe leading to the throttle body for structural breaches."},
    "other_sound": {"type": "diagnosis", "text": "DIAGNOSIS: Undefined mechanical acoustic signature. Requires physical inspection using a mechanic's stethoscope to isolate the source."},
    "diag_healthy": {"type": "diagnosis", "text": "DIAGNOSIS: Without definitive symptomatic parameters, the Engine and Transmission are assumed to be operating optimally. Ensure adherence to scheduled maintenance intervals."}}

# ==========================================
# INFERENCE ENGINE (Rule-Based Decision Tree)
# ==========================================
# This function acts as the core logical engine for our rule-based system.
# It receives the user's current position within the Knowledge Base (the node ID)
# and evaluates the branch to take based on the user's Boolean response (Yes/No).

def get_next_node(current_node_id, user_answer):
    # Step 1: Retrieve the current node definition from the Knowledge Base dictionary.
    current_node = diagnostic_kb.get(current_node_id)
    
    # Step 2: Safety Check. If the node doesn't exist, halt and return an error state.
    if not current_node:
        return {"type": "diagnosis", "text": "Error: Node not found in Knowledge Base.", "id": "error"}
        
    # Step 3: Forward Chaining Route Selection.
    # By analyzing the user's input, we determine the pointer to the next logical concept in the tree.
    if user_answer.lower() == 'yes':
        next_node_id = current_node.get('yes')
    else:
        next_node_id = current_node.get('no')
        
    # Step 4: Retrieve the next node payload.
    next_node_data = diagnostic_kb.get(next_node_id)
    
    # Step 5: Inject the node ID into the dictionary so the frontend 
    # can explicitly track its state in the overarching graph.
    if next_node_data:
        next_node_data['id'] = next_node_id 
        
    return next_node_data


# --- FLASK ROUTES ---

# Serves the main UI page
@app.route('/')
def index():
    return render_template('index.html')


# The API endpoint that acts as the interface to the Inference Engine
@app.route('/ask', methods=['POST'])
def ask_engine():
    data = request.json
    
    # Extract the current state from the incoming request payload
    current_node_id = data.get('current_node')
    user_answer = data.get('answer') # Expecting 'yes' or 'no'
    
    # If starting fresh, return the initial 'start' node without processing previous answers
    if not current_node_id or not user_answer:
        start_node = diagnostic_kb.get('start')
        start_node['id'] = 'start'
        return jsonify({"node": start_node})
        
    # Pass execution to the purely functional Inference Engine
    next_node = get_next_node(current_node_id, user_answer)
    
    return jsonify({"node": next_node})


if __name__ == '__main__':
    app.run(debug=True, port=8000)
