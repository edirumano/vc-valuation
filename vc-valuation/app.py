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