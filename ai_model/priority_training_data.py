"""
Training data for complaint priority prediction model.
Combines complaint text and category to predict priority level.
"""

PRIORITY_TRAINING_DATA = [
    # HIGH PRIORITY - Dangerous, Emergency, Safety Issues
    
    # Water - High Priority
    ("Water pipe burst on main road causing flooding", "Water", "high"),
    ("Sewage water overflowing near school", "Water", "high"),
    ("Contaminated water supply causing health issues", "Water", "high"),
    ("Major water leak near hospital entrance", "Water", "high"),
    ("Water tank collapsed dangerous situation", "Water", "high"),
    ("Drinking water contaminated urgent action needed", "Water", "high"),
    ("Sewage overflow near children playground", "Water", "high"),
    ("Water pipeline broken near school bus stop", "Water", "high"),
    ("Dirty water coming from tap health hazard", "Water", "high"),
    ("Water flooding on road causing accidents", "Water", "high"),
    
    # Electricity - High Priority
    ("Electric wire hanging dangerously on road", "Electricity", "high"),
    ("Transformer sparking near residential area", "Electricity", "high"),
    ("Exposed electric wire near school", "Electricity", "high"),
    ("Power pole fallen on road blocking traffic", "Electricity", "high"),
    ("Electric shock risk from broken wire", "Electricity", "high"),
    ("Transformer oil leaking fire hazard", "Electricity", "high"),
    ("Live wire touching tree dangerous", "Electricity", "high"),
    ("Electric pole damaged after accident", "Electricity", "high"),
    ("Short circuit causing fire risk", "Electricity", "high"),
    ("Broken electric cable near hospital", "Electricity", "high"),
    
    # Street Light - High Priority
    ("No street lights near school very dark", "Street Light", "high"),
    ("Street light pole fallen on footpath", "Street Light", "high"),
    ("All street lights off near hospital road", "Street Light", "high"),
    ("Dark street causing safety issues for women", "Street Light", "high"),
    ("Street light wire exposed dangerous", "Street Light", "high"),
    
    # Sanitation - High Priority
    ("Open manhole on main road very dangerous", "Sanitation", "high"),
    ("Sewage overflow near hospital creating health hazard", "Sanitation", "high"),
    ("Garbage dump near school health risk", "Sanitation", "high"),
    ("Blocked drain causing water logging and mosquitoes", "Sanitation", "high"),
    ("Overflowing sewage entering houses", "Sanitation", "high"),
    ("Open drain near children play area dangerous", "Sanitation", "high"),
    ("Waste water stagnation breeding mosquitoes dengue risk", "Sanitation", "high"),
    ("Manhole cover missing someone can fall", "Sanitation", "high"),
    ("Sewage leak near drinking water source", "Sanitation", "high"),
    ("Garbage burning causing air pollution health issue", "Sanitation", "high"),
    
    # Roads - High Priority
    ("Deep pothole on main road causing accidents", "Roads", "high"),
    ("Road collapsed after rain dangerous", "Roads", "high"),
    ("Big crater on road near school bus route", "Roads", "high"),
    ("Road damage near hospital ambulance route", "Roads", "high"),
    ("Bridge damaged unsafe for vehicles", "Roads", "high"),
    ("Road caved in dangerous for traffic", "Roads", "high"),
    ("Multiple potholes causing bike accidents", "Roads", "high"),
    ("Road surface broken near school", "Roads", "high"),
    ("Dangerous pothole caused accident yesterday", "Roads", "high"),
    ("Road completely damaged blocking emergency vehicles", "Roads", "high"),
    
    # Other - High Priority
    ("Stray dogs attacking people near school", "Other", "high"),
    ("Tree about to fall on house dangerous", "Other", "high"),
    ("Illegal construction blocking fire exit", "Other", "high"),
    ("Wall collapsed on footpath blocking path", "Other", "high"),
    ("Traffic signal not working causing accidents", "Other", "high"),
    
    # MEDIUM PRIORITY - Public Inconvenience, Needs Attention
    
    # Water - Medium Priority
    ("Water supply irregular in our area", "Water", "medium"),
    ("Low water pressure in taps", "Water", "medium"),
    ("Water supply only for 2 hours daily", "Water", "medium"),
    ("Water connection not working properly", "Water", "medium"),
    ("Need new water connection for house", "Water", "medium"),
    ("Water meter not working correctly", "Water", "medium"),
    ("Water supply timing needs to be fixed", "Water", "medium"),
    ("Public tap not working in our street", "Water", "medium"),
    ("Water tank needs cleaning", "Water", "medium"),
    ("Water motor making noise needs repair", "Water", "medium"),
    ("Small water leak from pipe", "Water", "medium"),
    ("Water bill is incorrect", "Water", "medium"),
    ("Water connection request pending", "Water", "medium"),
    ("Bore well pump not working", "Water", "medium"),
    ("Water supply schedule not followed", "Water", "medium"),
    
    # Electricity - Medium Priority
    ("Frequent power cuts in our area", "Electricity", "medium"),
    ("Power outage for 4 hours daily", "Electricity", "medium"),
    ("Voltage fluctuation damaging appliances", "Electricity", "medium"),
    ("Need new electricity connection", "Electricity", "medium"),
    ("Electric meter reading wrong", "Electricity", "medium"),
    ("Power supply irregular", "Electricity", "medium"),
    ("Electricity bill is too high", "Electricity", "medium"),
    ("Transformer making loud noise", "Electricity", "medium"),
    ("Power cut during evening hours", "Electricity", "medium"),
    ("Electricity connection approval pending", "Electricity", "medium"),
    ("Load shedding affecting work", "Electricity", "medium"),
    ("Power backup needed in area", "Electricity", "medium"),
    ("Electric pole needs maintenance", "Electricity", "medium"),
    ("Electricity supply unstable", "Electricity", "medium"),
    ("Power cut notification not received", "Electricity", "medium"),
    
    # Street Light - Medium Priority
    ("Some street lights not working", "Street Light", "medium"),
    ("Street light glowing dim", "Street Light", "medium"),
    ("Need more street lights in our lane", "Street Light", "medium"),
    ("Street light timing needs adjustment", "Street Light", "medium"),
    ("Street light bulb fused", "Street Light", "medium"),
    ("Street light switch not working", "Street Light", "medium"),
    ("Few street lights off in our area", "Street Light", "medium"),
    ("Street light maintenance required", "Street Light", "medium"),
    ("Street light flickering", "Street Light", "medium"),
    ("Street light cover broken", "Street Light", "medium"),
    ("Need LED street lights", "Street Light", "medium"),
    ("Street light pole rusted", "Street Light", "medium"),
    ("Street light not bright enough", "Street Light", "medium"),
    ("Street light installation pending", "Street Light", "medium"),
    ("Street light wiring needs repair", "Street Light", "medium"),
    
    # Sanitation - Medium Priority
    ("Garbage not collected for 2 days", "Sanitation", "medium"),
    ("Dustbin is full needs emptying", "Sanitation", "medium"),
    ("Garbage collection irregular", "Sanitation", "medium"),
    ("Need more dustbins in our area", "Sanitation", "medium"),
    ("Waste segregation not done properly", "Sanitation", "medium"),
    ("Garbage truck comes late", "Sanitation", "medium"),
    ("Drain needs cleaning", "Sanitation", "medium"),
    ("Bad smell from garbage dump", "Sanitation", "medium"),
    ("Public toilet needs cleaning", "Sanitation", "medium"),
    ("Garbage collection timing inconvenient", "Sanitation", "medium"),
    ("Waste disposal not regular", "Sanitation", "medium"),
    ("Drainage water slow", "Sanitation", "medium"),
    ("Garbage bin damaged", "Sanitation", "medium"),
    ("Sanitation worker not coming regularly", "Sanitation", "medium"),
    ("Drain cover missing", "Sanitation", "medium"),
    
    # Roads - Medium Priority
    ("Road has some potholes", "Roads", "medium"),
    ("Road needs repair", "Roads", "medium"),
    ("Road surface uneven", "Roads", "medium"),
    ("Small potholes on our street", "Roads", "medium"),
    ("Road tar work needed", "Roads", "medium"),
    ("Road maintenance required", "Roads", "medium"),
    ("Speed breaker damaged", "Roads", "medium"),
    ("Road marking faded", "Roads", "medium"),
    ("Road side drain needs repair", "Roads", "medium"),
    ("Road widening needed", "Roads", "medium"),
    ("Footpath broken", "Roads", "medium"),
    ("Road construction incomplete", "Roads", "medium"),
    ("Road divider damaged", "Roads", "medium"),
    ("Road needs resurfacing", "Roads", "medium"),
    ("Pavement stones loose", "Roads", "medium"),
    
    # Other - Medium Priority
    ("Park maintenance required", "Other", "medium"),
    ("Public bench broken", "Other", "medium"),
    ("Bus stop shelter damaged", "Other", "medium"),
    ("Community hall needs repair", "Other", "medium"),
    ("Playground equipment broken", "Other", "medium"),
    ("Public property needs maintenance", "Other", "medium"),
    ("Signboard fallen down", "Other", "medium"),
    ("Boundary wall needs repair", "Other", "medium"),
    ("Footpath encroachment", "Other", "medium"),
    ("Illegal parking problem", "Other", "medium"),
    ("Noise pollution from shop", "Other", "medium"),
    ("Street vendor blocking path", "Other", "medium"),
    ("Public toilet door broken", "Other", "medium"),
    ("Park gate not working", "Other", "medium"),
    ("Community center cleaning needed", "Other", "medium"),
    
    # LOW PRIORITY - Minor Issues, Can Wait
    
    # Water - Low Priority
    ("Water tap dripping slowly", "Water", "low"),
    ("Water connection form submission", "Water", "low"),
    ("Water bill payment query", "Water", "low"),
    ("Request for water connection", "Water", "low"),
    ("Water supply information needed", "Water", "low"),
    ("Water meter relocation request", "Water", "low"),
    ("Water connection name change", "Water", "low"),
    ("Water supply schedule query", "Water", "low"),
    ("Water quality test request", "Water", "low"),
    ("Water conservation suggestion", "Water", "low"),
    
    # Electricity - Low Priority
    ("Electricity bill payment query", "Electricity", "low"),
    ("Request for new connection form", "Electricity", "low"),
    ("Electricity meter reading query", "Electricity", "low"),
    ("Power cut schedule information", "Electricity", "low"),
    ("Electricity connection name transfer", "Electricity", "low"),
    ("Electricity bill duplicate copy", "Electricity", "low"),
    ("Power consumption query", "Electricity", "low"),
    ("Electricity tariff information", "Electricity", "low"),
    ("Meter reading correction request", "Electricity", "low"),
    ("Electricity connection documents", "Electricity", "low"),
    
    # Street Light - Low Priority
    ("Street light timing query", "Street Light", "low"),
    ("Request for new street light", "Street Light", "low"),
    ("Street light location suggestion", "Street Light", "low"),
    ("Street light energy saving suggestion", "Street Light", "low"),
    ("Street light design feedback", "Street Light", "low"),
    ("Street light installation query", "Street Light", "low"),
    ("Street light maintenance schedule", "Street Light", "low"),
    ("Street light complaint status", "Street Light", "low"),
    ("Street light upgrade request", "Street Light", "low"),
    ("Street light information needed", "Street Light", "low"),
    
    # Sanitation - Low Priority
    ("Garbage collection schedule query", "Sanitation", "low"),
    ("Request for additional dustbin", "Sanitation", "low"),
    ("Waste segregation information", "Sanitation", "low"),
    ("Garbage collection timing query", "Sanitation", "low"),
    ("Sanitation awareness program request", "Sanitation", "low"),
    ("Composting information needed", "Sanitation", "low"),
    ("Waste management suggestion", "Sanitation", "low"),
    ("Recycling facility query", "Sanitation", "low"),
    ("Sanitation worker contact details", "Sanitation", "low"),
    ("Garbage collection holiday schedule", "Sanitation", "low"),
    
    # Roads - Low Priority
    ("Road construction schedule query", "Roads", "low"),
    ("Request for speed breaker", "Roads", "low"),
    ("Road name board missing", "Roads", "low"),
    ("Road widening suggestion", "Roads", "low"),
    ("Footpath construction request", "Roads", "low"),
    ("Road maintenance schedule query", "Roads", "low"),
    ("Road marking request", "Roads", "low"),
    ("Parking space request", "Roads", "low"),
    ("Road design feedback", "Roads", "low"),
    ("Road information needed", "Roads", "low"),
    
    # Other - Low Priority
    ("General inquiry about services", "Other", "low"),
    ("Suggestion for improvement", "Other", "low"),
    ("Feedback on panchayath services", "Other", "low"),
    ("Request for information", "Other", "low"),
    ("Community event suggestion", "Other", "low"),
    ("Park beautification suggestion", "Other", "low"),
    ("Public facility feedback", "Other", "low"),
    ("Service appreciation", "Other", "low"),
    ("General complaint status query", "Other", "low"),
    ("Information about schemes", "Other", "low"),
]

# Priority labels
PRIORITY_LEVELS = ["high", "medium", "low"]

# Emergency keywords that indicate high priority
EMERGENCY_KEYWORDS = [
    'danger', 'dangerous', 'emergency', 'urgent', 'immediately', 'accident',
    'fire', 'injury', 'hurt', 'hospital', 'death', 'electrocution', 'shock',
    'flood', 'collapse', 'broken', 'immediate', 'critical', 'severe',
    'hazard', 'risk', 'unsafe', 'threatening', 'fatal', 'serious',
    'school', 'children', 'kids', 'student', 'ambulance', 'health',
    'attack', 'fall', 'fallen', 'burst', 'leak', 'overflow', 'block',
    'sparking', 'exposed', 'hanging', 'open manhole', 'contaminated'
]

# Location keywords that increase priority
HIGH_PRIORITY_LOCATIONS = [
    'school', 'hospital', 'clinic', 'dispensary', 'college', 'university',
    'playground', 'park', 'children', 'kids', 'main road', 'highway',
    'bus stop', 'railway', 'market', 'temple', 'church', 'mosque',
    'community center', 'public place', 'crowded area'
]
