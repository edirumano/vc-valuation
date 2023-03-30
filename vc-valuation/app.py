from flask import Flask, render_template, request

app = Flask(__name__, static_url_path='/static', static_folder='static')



class Investor:
    def __init__(self,investorID,  invested=0):
        self.investorID = investorID
        self.invested = invested
        self.cumdistributed = 0
    
class Common:
    def __init__(self, investorID, ranking=0, shares=0, active=1, distributed=0):
        self.holder = investorID
        self.ranking = ranking
        self.shares = shares
        self.active = active
        self.distributed = distributed
        self.type_name = "Common Stock"
        
    
    def calc_conversion_value(self, company_val, com_securities, pref_securities):
        if self.active == 1:
            return 0
        else:

   
class Preferred:
    def __init__(self, investorID, ranking, app, liqpref, distributed=0):
        self.holder = investorID
        self.ranking = ranking
        self.app = app
        self.liqpref = liqpref
        self.distributed = distributed
    

class InvestorSecurity:
    type_names = {"red_pref": "Redeemable Preferred", "part_pref": "Participating Preferred", "conv_pref": "Convertible Preferred"}
    
    def __init__(self, investorID, common=None, preferred=None, sec_type=None):
        self.holder = investorID
        self.common = common
        self.preferred = preferred
        self.sec_type = sec_type
        self.type_name = InvestorSecurity.type_names[sec_type]
        # self.cap = cap (define later and put in args)
        # self.QPO = QPO (define later and put in args)



def calculate_waterfall(InvestorSecurities, FounderShares, company_val):
    # Initialize the waterfall
    waterfall = []

    # Obtain the preferred securities in InvestorSecurities
    pref_securities = [sec.preferred for sec in InvestorSecurities if sec.preferred is not None]
    # Sort the pref_securities by their ranking from highest to lowest
    pref_securities.sort(key=lambda x: x.ranking, reverse=True)

    # Obtain the common securities in InvestorSecuritie
    com_securities = [sec.common for sec in InvestorSecurities if sec.common is not None]
    # Append the founder common shares to the common securities
    com_securities.append(FounderShares)

    # Calculate the total app * liqpref for all preferred securities
    total_pref_val = sum([sec.app * sec.liqpref for sec in pref_securities])

    #Initialize the distributable amount
    total_distributable = company_val

    # Distribute the company_val among the preferred securities
    for sec in pref_securities:
        # Distribute to each preferred security the app*liqpref up to distributable amount
        sec.distributed=min(sec.app * sec.liqpref, max(total_distributable,0))
        total_distributable -= sec.distributed
        waterfall.append([sec.holder,sec.ranking,sec.distributed])

    # Distribute the remaining amount to the common securities
    if (total_pref_val<company_val):
        # For each common associated with a conv_pref, calculate the comppany value at which it converts
        
        
    return waterfall


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

    # Initialize the founder and founder shares
    Founder = Investor(investorID="Founder")
    founder_com_shares = float(form_data.get('founder_common_shares',0))
    FounderShares   = Common(investorID=Founder.investorID, shares=founder_com_shares)

    # Initialize the VC investor
    VCInvestor = Investor(investorID="VC Investor")

    # Obtain Series A security data
    serA_sec_type = form_data.get('serA_sec_type',None)
    serA_app = float(form_data.get('serA_app',0))
    serA_liqpref = float(form_data.get('serA_liqpref',0))
    serA_shares = float(form_data.get('serA_shares',0))

    # Initialize the Series A security
    seriesA_pref = Preferred(investorID=VCInvestor.investorID, ranking=1, app=serA_app, liqpref=serA_liqpref)
    if serA_sec_type == "red_pref":
        seriesA_com = None
    else:
        seriesA_com = Common(investorID=VCInvestor.investorID, shares=serA_shares)
        if serA_sec_type == "conv_pref":
            seriesA_com.active = 0
    SeriesA = InvestorSecurity(investorID=VCInvestor.investorID, common=seriesA_com, preferred=seriesA_pref, sec_type=serA_sec_type)
    
    company_val = float(form_data.get('company_val',1000))

    InvestorSecurities= [SeriesA]
    waterfall = calculate_waterfall(InvestorSecurities, FounderShares, company_val)

    return render_template('response.html', form=request.form, Founder=Founder, VCInvestor=VCInvestor, FounderShares=FounderShares, SeriesA=SeriesA,waterfall=waterfall)





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