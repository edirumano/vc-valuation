from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt # for plotting
import matplotlib.cm as cm #for color mapping
import time

app = Flask(__name__, static_url_path='/static', static_folder='static')

class Investor:
    def __init__(self, invID, name, gppercent=0,fees=0,comcap=0):
        self.invID = invID
        self.name = name
        self.gppercent = gppercent
        self.fees = fees
        self.comcap = comcap
        self.invested = 0
        self.invdistributed = 0

        

class Security:
    type_names = {"com": "Common Stock", "red_pref": "Redeemable Preferred", "part_pref": "Participating Preferred", "conv_pref": "Convertible Preferred"}

    def __init__(self, secID, holder, type="com", comshares=0, app=0, liqpref=0, ranking=1):
        self.secID = secID
        self.holder = holder
        self.type = type
        self.type_name = Security.type_names[type]
        self.comshares = comshares
        self.app = app
        self.liqpref = liqpref
        self.redeemval = self.app * self.liqpref
        self.ranking = ranking
        self.secdistributed = 0
        # Check if the security is convertible and set active to 0 if it is
        if self.type=="conv_pref":
            self.active = 0
            self.rvps = self.redeemval / self.comshares
        else:
            self.active = 1
        self.dumactive = self.active


def initialize_investors(form_data, total_investors):
    # initialize_investors takes the form data and the total number of investors and returns a list of investor objects
    
    investors = []
    
    for i in range(total_investors+1):
        # obtain the relevant data
        name = form_data.get(f'investors[{i}].name', "Investor " + str(i))
        gppercent = float(form_data.get(f'investors[{i}].gppercent', 0))
        fees = float(form_data.get(f'investors[{i}].fees', 0))
        comcap= float(form_data.get(f'investors[{i}].comcap', 0))
           
        # Create the investor object
        investors.append(Investor(i, name, gppercent, fees, comcap))

    return investors

def initalize_securities(form_data, total_securities, investors):
    # initialize_securities takes the form data and the total number of securities and returns a list of security objects
    
    securities = []
    
    for i in range(total_securities+1):
        # Obtain relevant data
        holder = investors[i].name # Later have this be chosen by the user
        type = form_data.get(f'securities[{i}].type', "com")
        comshares = float(form_data.get(f'securities[{i}].comshares', 0))
        app = float(form_data.get(f'securities[{i}].app', 0))
        liqpref = float(form_data.get(f'securities[{i}].liqpref', 0))
        ranking = i # Later have this be chosen by the user

        # Create the security object
        securities.append(Security(i,holder, type, comshares, app, liqpref, ranking))
    
    return securities

# Need to revise this in accordance with Zandberg's conversion calculation
def calculate_waterfall(investors, securities, company_val):

    # Waterfall initialized so that columns are company value then cumdist for each security
    # first row contains the secID of the security in that column, second row is all 0 (start of waterfall)
    waterfall = np.zeros((2,len(securities)+1))
    for i in range(len(securities)):
        waterfall[0][i+1] = securities[i].secID
   
    # Start with redeeming preferred
    preferred = []
    # obtain the preferred securities and associated secID, redemption val and rankings
    for sec in securities:
        if sec.redeemval > 0:
             pref = [sec.secID, sec.redeemval, sec.ranking]
             preferred.append(pref)

    # Generate dictionary of each ranking and the sum of redeemval for that ranking, plus total redeemval
    rankings_dict = {}
    total_rv = 0
    for pref in preferred:
        ranking = pref[2]
        redeemval = pref[1]
        if ranking in rankings_dict:
            rankings_dict[ranking] += redeemval
        else:
            rankings_dict[ranking] = redeemval 
        total_rv += redeemval

    # populate waterfall for each distinct preferred ranking
    for ranking in sorted(rankings_dict.keys(), reverse=True):
        new_row = np.copy(waterfall[-1, :])
        new_row[0] += rankings_dict[ranking]
        for sec in securities:
            if sec.ranking == ranking:
                new_row[sec.secID+1] += sec.redeemval
        waterfall = np.vstack([waterfall, new_row])

    # Sum the total active common shares
    total_active_common = 0
    com_to_convert = []
    for sec in securities:
        if sec.active == 1:
            total_active_common += sec.comshares
        else:
            secID = sec.secID
            rv = sec.redeemval
            com = sec.comshares
            rvps = sec.rvps
            new_row = {'secID': secID, 'redeemval': rv, 'comshares': com, 'rvps': rvps, 'conv_value': ''}
            com_to_convert.append(new_row)
    
    # Calculate conversion threshold for each convertible security
    com_to_convert = sorted(com_to_convert, key=lambda x: x['rvps'])
    convertedRV = 0
    dummy_active_common = total_active_common
    for sec in com_to_convert:
        conv_value = sec['redeemval']*((dummy_active_common + sec['comshares'])/sec['comshares'])+(total_rv - convertedRV - sec['redeemval'])
        sec['conv_value']=conv_value
        dummy_active_common += sec['comshares']
        convertedRV += sec['redeemval']
        

    # Distribute value until all inactive common shares are converted
    for conv_pref in com_to_convert:
        # Obtain the last waterfall row with cum dist values
        last_row = np.copy(waterfall[-1, :])
        # Copy for new row
        new_row = last_row.copy()
        # Set the company value to the first conversion threshold
        new_row[0] = conv_pref['conv_value']
        # Calculate the value distributable in this segment
        value_dist = new_row[0] - last_row[0]
        for sec in securities:
            if sec.dumactive == 1:
                new_row[sec.secID+1] += value_dist * (sec.comshares/total_active_common)
            else:
                if sec.secID == conv_pref['secID']:
                    sec.dumactive = 1
                    total_active_common += sec.comshares
        waterfall = np.vstack([waterfall, new_row])

    # Add 20% to last entry to see continuation if company value is smaller than last conversion threshold
    last_row = np.copy(waterfall[-1, :])
    new_row = last_row.copy()
    # Set the company value to the first conversion threshold
    if new_row[0] > company_val:
        new_row[0] = last_row[0]*1.2
    else:
        new_row[0]=company_val    
    value_dist = new_row[0] - last_row[0]
    for sec in securities:
        if sec.dumactive == 1:
            new_row[sec.secID+1] += value_dist * (sec.comshares/total_active_common)
    waterfall = np.vstack([waterfall, new_row])

    return waterfall


def create_waterfall_chart(waterfall, securities, timestamp):
    # Assume the first column is the x axis and the other columns are line series
    x = waterfall[:, 0]
    y_list = [waterfall[:, i] for i in range(1, waterfall.shape[1])]

#    Set the figure size and font properties
    plt.figure(figsize=(7, 3))
    plt.rcParams.update({'font.size': 8, 'font.family': 'serif'})
    plt.subplots_adjust(bottom=0.2)

    # Plot each line series with a different color
    num_colors = len(securities)  
    color_map = cm.get_cmap('tab20', num_colors)  # choose a colormap and number of colors
    colors = color_map.colors  # get a list of colors
    for i, y in enumerate(y_list):
        plt.plot(x, y, color=colors[i], label='{}, {}'.format(securities[i].type_name, securities[i].holder))

    # Set the x and y axis labels and title
    plt.xlabel('Company Valuation')
    plt.ylabel('Cumulutive Distibution to Security')
    plt.title('Waterfall: All Securities')

    # Add a legend to the chart
    plt.legend(loc='upper left')

    # Save the chart as a png file
    filename = f"static/charts/wf_all_{timestamp}.png"  # Adds timestamp to filename
    plt.savefig(filename)



def has_attribute(obj, attr):
    return hasattr(obj, attr)

# Add hasattr to the Jinja2 environment
app.jinja_env.globals.update(hasattr=has_attribute)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST',])
def submit():
    # Obtain the form data as a dictionary
    form_data = request.form.to_dict()

    # Set total investors and total securities (counting from 0)
    total_investors = 2 # Later have this be chosen by the user
    total_securities = 2 # Later have this be chosen by the user

    # Initialize the investors and securities
    investors = initialize_investors(form_data, total_investors)
    securities = initalize_securities(form_data, total_securities, investors)

    # Obtain the company valuation
    company_val = float(form_data.get('company_val',1000))

    # Calculation the waterfall
    waterfall = calculate_waterfall(investors, securities, company_val)

    # Create unique timestamp for the images
    timestamp = int(time.time())

    # Create the waterfall chart
    create_waterfall_chart(waterfall, securities, timestamp)

    return render_template('response.html', investors=investors, securities=securities, company_val = company_val, waterfall=waterfall,ts=timestamp)



'''

Investor
    InvestorID
    distributed = (#)
    invested = (#)
    [GP & LP Fund issues]

commmon
    Invetor = ID
    ranking = 0
    shares = (#)
    active = yes/no
    contignecy = if TotalVal/TotalCommon >= InvestorD.distributed, then active else not active
    distributed = (#)

pref
    Investor = ID
    rankikng = (#>0)
    app = (#)
    liqpref = (#)
    distributed = (#)
     
Seniority Structure
    [rank, complete]
    [0,never]
    [1,yes/no]
    [2,yes/no]

General waterfall algorithm: 
start with highest ranking (always will be a pref)
start with 0 company valuation 
if current rank filled != yes:
    increment valuation by 0.1
    if valuation > max_val
        end
    if current rank = 0 (i.e., commmon):
        determine if each common is active in this distribution
        calculate amount to distribute to each active holder
        for each active holder
            reduce the reamining by 0.1*holder distribution%
            increase total to holder by 0.1*holder distribution%
    if current rank >1 (i.e.,pref):
       reduce pref remaining by 0.1
       increase total to pref holder by 0.1
    
    if the remaining is at or below 0
        save remaining to 0
        change filled to yes
        current rank = current rank - 1


# start with pref
    collect all the pref, app and liqpref, sort by ranking
    distribute to the pref until the pref is filled

# then move to commmon
    collect all the commmon, active and inactive
    if any inactive, check whether they should be made active prior to the distribution
    distribute to the active commmon until company val is done

# then summarize distributions by security and holder

        
        
Keep track:
- total distributions at company val
- whether holder participatted in distributions at particular increment
- which security of the holder participated in distribution at particular increment 


determining if common is active in the distribution:
    [for the start, maybe just start with whether the fully-diluted amount equals the amount totally distributed]
    [then can figure out how to factor in prefs that outrank you]
    this is probably where all the action is; for convertible preferreds should be easy, for securities with a cap or QPO then might need contigencies...
    
this solves:
commmon [common yes, pref no]
RP [common no, pref yes]
RP + Commmon [common yes, pref yes]
CP [common maybe, pref yes]

Need to still solve:
PCP [commmon yes, pref maybe]
PCPC [common maybe, pref maybe]


for that security, disregard the pref and assume it is an always active commmon
run the waterfall analysis with that in mind and keep track of total distributions at each val point
active if total distributions to common >= total distributions to security otherwise 


For each security with a conversion, cap or QPO:

Start with highest ranked security and assume it's all common 
 issue is the contigencies with other potentially converting instruments.. 


RP - pref not contingent, no common
CP - pref not contingnet, common contingent



PCP
    contingent between CP and commmon 

contingency will always be at a company valuation 

Security
    common
    pref
    structure
        type = 0, 1, 2, 3 (common, RP, RP+C, CP, PCP, PCPC)
        cap = (#)
        QPO = (#)       

Given a company_val, and a list of Securities:
    Start with highest ranking
    Fill until app*liqpref is filled
    Move to next highest ranking
    If it is a preferred stock:
        fill until app*liqpref is filled
    If it is common:
        Split remaining among the fully-diluted common 

    Sum what each Security received


Let's say we have common + convertible preferred, then the conv_pref is = [common, redpref]

so the list of securities is iether:
[redpref, common]
[common, common]


[redpref, C1, C1+C2]

[C1+C2]

Measure redpref and common receives in each scenario
For conv_pref: 
    Pick the scenario that has the maximum to the conv_pref
    the scenario in which you choose common is "conversion" 

For PCP:
    If the valuation of the company is above the QPO threshold, then do only common and forget redpref

For PCP with cap:
    If the redpref has been active, then the total distributions cannot be more than the cap
    Simulatenously test if redpref didn't exist and just common and use this when its total
    distributions are more than the cap 

Then do this for each $1 or each $0.1 until some value

Chart the total amount distributed to common and conv_pref at each valuation

'''