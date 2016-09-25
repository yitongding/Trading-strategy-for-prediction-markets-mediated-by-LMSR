import random
from matplotlib import pyplot as pyplot
import traders
import run_experiments
import plot_simulation
import other_bots
import numpy
import simulation
import prices

from numpy import average
from warnings import catch_warnings
windowSize = 20
import information
class MyBot(traders.Trader):
    name = 'my_bot'
    myGuess = []
    def simulation_params(self, timesteps,
                          possible_jump_locations,
                          single_jump_probability):
        """Receive information about the simulation."""
        # Number of trading opportunities
        self.timesteps = timesteps
        # A list of timesteps when there could be a jump
        self.possible_jump_locations = possible_jump_locations
        # For each of the possible jump locations, the probability of
        # actually jumping at that point. Jumps are normally
        # distributed with mean 0 and standard deviation 0.2.
        self.single_jump_probability = single_jump_probability
        # A place to store the information we get
        self.information = []
        self.lastJumpIndex = 0
        self.diffMovingAvg = []
        self.useAvg = 0
        #graph drawing
        self.all_guess=[]
        self.market_belief=[]
        self.buy_price=[]
        self.sell_price=[]
        self.count=0
        self.guessjump=[0]
        self.marketPrice = []  
        
        self.allbelief=[]
    def slope_cal(self,pola,bigrange,jumps):
        index=jumps.index(pola)
        start = 1
        if (index-start)<5 or (bigrange-index)<5:
            return 0.0
        leftside=min(index-start,15)
        rightside=min(bigrange-index,15)
        left=0.0
        right=0.0
        for i in range(3):
            lefind=max(index-((i+1)/3)*leftside,0)
            rigind=min(index+((i+1)/3)*rightside,bigrange-1)
            left+=pola-jumps[lefind]
            right+=pola-jumps[rigind]
        tem=left*right
        return tem
    def determine_slop(self,small,smalid,large,largid):
        if small == 0 :
            if large > 2.8:
                #print 'lower value jump is zero','higher value jump is',large
                return largid
            else:
               # print 'both val are extremely small'
                return -1
        elif large==0:
            if small >2.8:
               # print 'higher value jump is zero','lower value jump is ',small
                return smalid
            else:
               # print 'both val are very small'
                return -1
        if (small/large)>3:
            return smalid
        elif (large/small)>3:
            return largid
        else:
            return -1
    def find_jumping(self):
        workout=[]
        pm=average(self.information)
        myjump=[0]
        for i in range(len(self.information)):
            if i==0:
                continue
            myjump.append((myjump[i-1]+self.information[i]-pm))
        minval=min(myjump)
        maxval=max(myjump)
        indemin=myjump.index(minval)
        indemax=myjump.index(maxval)
        minval=self.slope_cal(minval,len(self.information), myjump)  
        maxval=self.slope_cal(maxval,len(self.information), myjump)
        vak=self.determine_slop(minval,indemin,maxval,indemax)
        if vak==-1:
            workout.append(-1)
        else:
            #print 'there is a up jump at ',vak,'step'
            workout.append(vak)
            prev=average(self.information[:vak])
            postv=average(self.information[vak:])
            workout.append(prev)
            workout.append(postv)
        return workout
    def new_information(self, info, time):
        """Get information about the underlying market value.
        
        info: 1 with probability equal to the current
          underlying market value, and 0 otherwise.
        time: The current timestep for the experiment. It
          matches up with possible_jump_locations. It will
          be between 0 and self.timesteps - 1."""
        self.information.append(info)
    def trades_history(self, trades, time):
        #since that the market price would track the true price, and my guess is also guessing the true value. 
        #Thus what I am really guessing is what the market price will be 
        """A list of everyone's trades, in the following format:
        [(execution_price, 'buy' or 'sell', quantity,
          previous_market_belief), ...]
        Note that this isn't just new trades; it's all of them."""
        self.trades = trades
     
    def find_best_quantity(self, quantity, stride, tradeString, check_callback):
        if quantity == 0:
            return 0, 0

        stride = stride / 2

        if stride == 0:
            if tradeString == 'buy':
                return quantity, quantity*(self.useAvg - check_callback(tradeString, quantity))
            else:
                return quantity, quantity*(check_callback(tradeString, quantity) - self.useAvg)

        qtyL = quantity-stride
        qtyR = quantity+stride
        profitL = 0
        profitR = 0

        if qtyL > 0:
            qtyL, profitL = self.find_best_quantity(quantity-stride, stride, tradeString, check_callback)
        if qtyR > 0:
            qtyR, profitR = self.find_best_quantity(quantity+stride, stride, tradeString, check_callback)

        if profitL > profitR:
            return qtyL, profitL
        else:
            return qtyR, profitR
        
    def trading_opportunity(self, cash_callback, shares_callback,
                            check_callback, execute_callback,
                            market_belief):
        """Called when the bot has an opportunity to trade.
        cash_callback(): How much cash the bot has right now.
        shares_callback(): How many shares the bot owns.
        check_callback(buysell, quantity): Returns the per-share
          price of buying or selling the given quantity.
        execute_callback(buysell, quantity): Buy or sell the given
          quantity of shares.
        market_belief: The market maker's current belief.
        Note that a bot can always buy and sell: the bot will borrow
        shares or cash automatically.
        """
        size = 3
        self.marketPrice.append(market_belief) #ADDED
        #belief update
        currentbelief=0
        if len(self.information)>40:
            tempo=self.find_jumping()
            if tempo[0]-self.guessjump[-1] >4:
                self.guessjump.append(tempo[0])
            elif len(self.guessjump)>1:
                mostrecent=self.guessjump[-1]
                currentbelief=average(self.information[mostrecent:])
            elif len(self.guessjump)==1:
                currentbelief=average(self.information)                
        else:
            currentbelief=average(self.information)
        self.allbelief.append(currentbelief)
        
        #pric=information.getrealprice()
        #if len(pric)==100:
           # akk=list(range(1,101))
            #print 'price',len(pric)
           # print 'my guess',len(self.allbelief)
           # plt.plot(akk,pric)
            #plt.plot(akk,self.allbelief)
           # plt.show()
        bestAction = 'buy'
        avg = numpy.average(self.information)
        current_ave = numpy.average(self.marketPrice[-size:]) 
        self.useAvg = avg*100
        #self.useAvg = 0.2*avg*100 + current_ave*0.8
        self.useAvg = 0.2*currentbelief * 100 + current_ave*0.8

        self.myGuess.append(self.useAvg)
        
        #self.all_guess.append(self.useAvg)
        self.market_belief.append(market_belief)
        bestQuantity = 0
        rangeStride = 10
        quantity = 15
        bestBuyQuantity, buyDiff = self.find_best_quantity(quantity, rangeStride, 'buy', check_callback)
        bestSellQuantity, sellDiff = self.find_best_quantity(quantity, rangeStride, 'sell', check_callback)
        self.buy_price.append(check_callback('buy',bestBuyQuantity))
        self.sell_price.append(check_callback('sell',bestSellQuantity))
        diff=[]
        for i in range(len(self.market_belief)):
            if i==0:
                continue
            diff.append(self.market_belief[i]-self.market_belief[i-1])
        '''
        if len(self.market_belief) >99:
            print 'market belief',len(self.market_belief),self.market_belief
            print 'my guess',len(self.all_guess),self.all_guess
            print 'best Buy price',len(self.buy_price),self.buy_price
            print 'best sell price',len(self.sell_price),self.sell_price
            print 'diff',diff
        '''
        if sellDiff > buyDiff:
            bestQuantity = bestSellQuantity
            bestAction = 'sell'
        else:
            bestQuantity = bestBuyQuantity
            bestAction = 'buy'
        # Trade in the best way, if a beneficial trade was found
        if bestQuantity > 0:
            # print "Buying or selling? " + bestAction
            execute_callback(bestAction, bestQuantity)
        


def plot_beliefs2(beliefs, color='k'):
    belief_by_time = {}
    for time, belief in beliefs:
        belief_by_time.setdefault(time, []).append(belief)
    x = belief_by_time.keys()
    y = [sum(a) / float(len(a)) for a in belief_by_time.values()]
    pyplot.plot(x, y, color=color)
    return x
 
    
       
def plotOnce():
    bots = [MyBot()]
    bots.extend(other_bots.get_bots(5, 2))
    #bots.extend(other_bots.get_bots(num_fundamentals, num_technical))
    
    # Plot a single run. Useful for debugging and visualizing your
    # bot's performance. Also prints the bot's final profit, but this
    # will be very noisy.
    
    
    lmsr_b=150
    market_fact = prices.LMSRFactory(lmsr_b)
    #market_fact = 0
    timesteps=100
    sim_obj = simulation.Simulation(
        timesteps, market_fact, bots)
    
    #sim_obj = plot_simulation.run(bots)
    #print sim_obj.p_vec
    sim_obj.simulate()
    pyplot.figure()
    x_overall = plot_beliefs2(sim_obj.log.beliefs) 
    pyplot.plot(range(len(sim_obj.p_vec)),[a * 100.0 for a in sim_obj.p_vec],ls='--', color='r')
    pyplot.plot(range(len(bots[0].myGuess)),[a for a in bots[0].myGuess], color='b')
    pyplot.ylim((0, 100))
    pyplot.show()
       
def main():
    bots = [MyBot()]
    bots.extend(other_bots.get_bots(0, 10))
    # bots.extend(other_bots.get_bots(num_fundamentals, num_technical))
    
    # Plot a single run. Useful for debugging and visualizing your
    # bot's performance. Also prints the bot's final profit, but this
    # will be very noisy.
    plot_simulation.run(bots)
    
    # Calculate statistics over many runs. Provides the mean and
    # standard deviation of your bot's profit.
    #run_experiments.run(bots, num_processes=6, simulations=5000, lmsr_b=150)
    
    #plotOnce()
    
    
# Extra parameters to plot_simulation.run:
#   timesteps=100, lmsr_b=150

# Extra parameters to run_experiments.run:
#   timesteps=100, num_processes=2, simulations=2000, lmsr_b=150

# Descriptions of extra parameters:
# timesteps: The number of trading rounds in each simulation.
# lmsr_b: LMSR's B parameter. Higher means prices change less,
#           and the market maker can lose more money.
# num_processes: In general, set this to the number of cores on your
#                  machine to get maximum performance.
# simulations: The number of simulations to run.
if __name__ == '__main__': # If this file is run directly
    main()