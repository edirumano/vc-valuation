from flask import Flask, render_template, request

app = Flask(__name__)


class Investor:
    def __init__(self,investorID, cumdistributed, invested):
        self.investorID = investorID
        self.cumdistributed = cumdistributed
        self.invested = invested
    
class Common:
    def __init__(self, investorID, ranking, shares, active, distributed):
        self.holder = investorID
        self.ranking = ranking
        self.shares = shares
        self.active = active
        self.distributed = distributed

class Preferred:
    def __init__(self, investorID, ranking, app, liqpref, distributed):
        self.holder = investorID
        self.ranking = ranking
        self.app = app
        self.liqpref = liqpref
        self.distributed = distributed

class Security:
    valid_sec_types = ["red_pref", "red_pref_common", "conv_pref"]

    def __init__(self, common=None, preferred=None, sec_type=None):
        self.common = common
        self.preferred = preferred
        self.sec_type = sec_type
        # self.cap = cap (define later and put in args)
        # self.QPO = QPO (define later and put in args)

        if self.sec_type not in self.valid_sec_types:
            raise ValueError("Invalid security type")
    

# Set initial investors consititng of Founder and VC Investor
Founder = Investor("Founder",cumdistributed=0,invested=0)
VCInvestor = Investor("VC Investor",cumdistributed=0,invested=0)

# Set initial underlying securities consisting of common and preferred
founder_shares   = Common("Founder",ranking=0,shares=100,active=1,distributed=0)
seriesA_pref = Preferred("VC Investor",ranking=1,app=50,liqpref=1.5,distributed=0)
seriesA_common = Common("VC Investor",ranking=0,shares=10,active=0,distributed=0)

# Series A security consits of a common and preferred; the common is contingent on the preferred
seriesA = Security(common=seriesA_common, preferred=seriesA_pref, sec_type="conv_pref")


# obtain the total common shares from founder and series A investor
total_common = founder_shares.shares + seriesA.common.shares

# print the total commoon shares
print("Total Common Shares: ", total_common)


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
... issue is the contigencies with other potentially converting instruments.. 


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
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST',])
def submit():

    # Container 1: Obtain values of all securities submitted in previous page

    # Container 2: Calculate returns for all securities 

    # Container 3: Generate charts

    # Container 4: Goal-seek/iterate to find optimal values for certain attributes 

    value = float(request.form['value'])
    shares = float(request.form['shares'])
    result = value * shares
    return render_template('response.html', form=request.form, result=result)