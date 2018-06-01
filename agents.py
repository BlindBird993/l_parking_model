from mesa import Agent, Model
import random
import numpy as np

class TradeInterface(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)
        self.hour = 0
        self.day = 0
        self.week = 0

        self.buyers = []
        self.sellers = []
        self.demands = []
        self.productions = []
        self.demandPrice = []
        self.supplyPrice = []

        self.historyDemands = []
        self.historyProductions = []
        self.historyOutPrice = []

        self.distributedDemands = []
        self.summedDemands = []

        self.buyerPriceList = []
        self.clearPriceList = []
        self.satisfiedDemands = []

        self.demandCount = 0

        self.dealCount = 0
        self.noDealCount = 0

        self.dealsList = []
        self.noDealsList = []

        self.buyerPrices = []
        self.sellerPrices = []

        self.clearPrice = 0

        self.outPrice = 0

        self.currentSeller = 0
        self.currentBuyer = 0

        self.numberOfBuyers = 0
        self.numberOfSellers = 0

    def getOuterPrice(self):
        self.outPrice = 200
        priceList = []
        for i in range(50,310,10):
            priceList.append(i)
        averagePrice = np.mean(priceList)
        priceCoeff = 1.5
        if self.hour >= 7 and self.hour <= 9:
            self.outPrice = averagePrice*priceCoeff
        elif self.hour >= 15 and self.hour <= 17:
            self.outPrice = averagePrice * priceCoeff
        else:
            self.outPrice = averagePrice
        self.historyOutPrice.append(self.outPrice)
        print("Outer Price {}".format(self.outPrice))

    def getSellers(self):
        self.numberOfSellers = 0
        self.sellers = []
        for agent in self.model.schedule.agents:
            if (isinstance(agent, ParkingSlotAgent)):
                if agent.readyToSell is True:
                    self.numberOfSellers += 1
                    self.sellers.append(agent.unique_id)
                    print("Sellers {}".format(agent.unique_id))
        self.historyProductions.append(self.numberOfSellers)
        print("List of sellers {}".format(self.sellers))
        print("Number of sellers {}".format(self.numberOfSellers))

    def getBuyres(self):
        self.numberOfBuyers = 0
        self.buyers = []
        for agent in self.model.schedule.agents:
            if (isinstance(agent, CarAgent)):
                if agent.readyToBuy is True:
                    self.numberOfBuyers += 1
                    self.buyers.append(agent.unique_id)
                    print("Buyers {}".format(agent.unique_id))
        self.historyDemands.append(self.numberOfBuyers)
        print("List of buyers {}".format(self.buyers))
        print("Number of buyers {}".format(self.numberOfBuyers))

    def calculateBuyerReward(self,buyer,price):
        priceList = buyer.setOfPrices
        max_val = max(priceList)
        outPriceNorm = self.outPrice/max_val
        priceNorm = price/max_val
        priceDiff = round(outPriceNorm-priceNorm,3)*100
        if priceDiff < 0:
            priceDiff = 0.0
        return priceDiff

    def calculateSellerReward(self,seller,price):
        priceList = seller.setOfPrices
        max_val = max(priceList)
        priceNorm = price/max_val
        priceRewardNorm = round(priceNorm,3)
        priceRewardNorm  = priceRewardNorm * 100
        return priceRewardNorm

    def chooseSeller(self,buyer,price = None,amount = None):
        seller = np.random.choice(self.sellers)
        for agent in self.model.schedule.agents:
            if (isinstance(agent, ParkingSlotAgent)):
                if agent.readyToSell is True and agent.unique_id == seller:
                    print("Seller {}".format(agent.unique_id))
                    print("Seller price {}".format(agent.price))

                    if buyer.price >= agent.price:
                        print("Deal !")

                        priceList = agent.setOfPrices
                        print("Price List {}".format(priceList))

                        self.clearPrice = round(np.mean([agent.price, buyer.price]),1)
                        print("Clear price {}".format(self.clearPrice))

                        agent.status = 'busy'
                        agent.readyToSell = False
                        agent.busyTime = buyer.parkingTime

                        buyer.status = 'busy'
                        buyer.readyToBuy = False
                        buyer.busyTime = buyer.parkingTime

                        print("Car busy time {}".format(buyer.busyTime))
                        print("Slot busy time {}".format(agent.busyTime))

                        buyer_reward = self.calculateBuyerReward(buyer,buyer.price)
                        seller_reward = self.calculateSellerReward(agent,agent.price)

                        print("Buyer reward {}".format(buyer_reward))
                        print("Seller reward {}".format(seller_reward))

                        #update learning data for buyer
                        print("Agent {} old price propensities {}".format(buyer.unique_id,buyer.pricePropensities))
                        print("Agent {} price probabilities {}".format(buyer.unique_id,buyer.priceProbs))
                        buyer.updatePricePropensities(buyer_reward)
                        buyer.updatePriceProbabilities()
                        print("Agent {} new price propensities {}".format(buyer.unique_id,buyer.pricePropensities))
                        print("Agent {} new price probabilities {}".format(buyer.unique_id,buyer.priceProbs))

                        #update learning data for seller
                        print("Agent {} old price propensities {}".format(agent.unique_id,agent.pricePropensities))
                        print("Agent {} price probabilities {}".format(agent.unique_id,agent.priceProbs))
                        agent.updatePricePropensities(seller_reward)
                        agent.updatePriceProbabilities()
                        print("Agent {} new price propensities {}".format(agent.unique_id,agent.pricePropensities))
                        print("Agent {} new price probabilities {}".format(agent.unique_id,agent.priceProbs))

                        #write to queue
                        agent.queue.append(buyer.unique_id)

                        self.buyerPrices.append(buyer.price)
                        self.sellerPrices.append(agent.price)

                        self.dealCount += 1
                        self.clearPriceList.append(self.clearPrice)

                        self.numberOfBuyers -= 1
                        self.numberOfSellers -= 1

                        self.demandCount += 1

                        self.buyers.remove(buyer.unique_id)
                        self.sellers.remove(agent.unique_id)

                        print("Number of sellers {}".format(self.numberOfSellers))
                        print("Number of buyers {}".format(self.numberOfBuyers))
                    else:
                        print('No deal')
                        self.noDealCount += 1
                        buyer.updatePricePropensities(0.0)
                        buyer.updateCriticalPropensities()
                        buyer.updatePriceProbabilities()
                        buyer.choosePrice()

                        agent.updatePricePropensities(0.0)
                        agent.updateCriticalPropensities()
                        agent.updatePriceProbabilities()
                        agent.choosePrice()
                        print("Old price propensities {}".format(buyer.pricePropensities))
                        print("Price probabilities {}".format(buyer.priceProbs))

    def distributeParking(self):
        self.sellPrice = 0
        self.buyPrice = 0
        self.demandCount = 0
        self.dealCount = 0
        self.noDealCount = 0
        while(not(self.numberOfSellers <= 0 or self.numberOfBuyers <= 0)):
            buyer_id = np.random.choice(self.buyers)
            print("Buyer Random ID {}".format(buyer_id))
            for agent in self.model.schedule.agents:
                if (isinstance(agent, CarAgent) and agent.readyToBuy is True):
                    if agent.unique_id == buyer_id:
                        self.buyPrice = agent.price
                        print("Buyer {}".format(agent.unique_id))
                        print("Buy price {}".format(agent.price))
                        agent.choosePrice()
                        self.chooseSeller(agent)


        self.satisfiedDemands.append(self.demandCount)

        if self.numberOfBuyers > 0 and self.numberOfSellers == 0:
            print("Not enough place")
            car_list = []
            for agent in self.model.schedule.agents:
                if (isinstance(agent, CarAgent)):
                    if agent.readyToBuy is True:
                        car_list.append(agent.unique_id)
            print("Cars left {}".format(car_list))


        elif self.numberOfBuyers == 0 and self.numberOfSellers > 0:
            print("Place left")

        else:
            print("No sellers and No buyers")
        self.dealsList.append(self.dealCount)
        self.noDealsList.append(self.noDealCount)

    def step(self):
        self.getBuyres()
        self.getSellers()
        self.getOuterPrice()
        self.distributeParking()
        self.hour += 1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class CarAgent(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)
        self.hour = 0
        self.day = 0
        self.week = 0
        self.statusPriority = None
        self.needToWash = False
        self.wantToPark = True
        self.traided = None
        self.parkingTime = 0

        self.busyTime = 0

        self.status = 'free'

        self.priceHistory = []
        self.priorityHistorySell = []
        self.priorityHistoryBuy = []

        self.readyToSell = False
        self.readyToBuy = True
        self.initial_step = True

        self.memory_param = 0.8
        self.experimental_param = 0.5

        self.setOfPrices = []
        self.pricePropensities = []
        self.priceProbs = []
        self.initialPropensities = []

        self.price = 0
        self.priceChoice = 0
        self.choice = 0
        self.stateChoice = None

    def updateCriticalPropensities(self):
        print("Propensity update")
        for index,elem in enumerate(self.pricePropensities):
            self.pricePropensities[index] = round(elem * 0.9, 3)
            self.pricePropensities[index] = elem + 0.1

    def choosePrice(self):
        if self.readyToBuy is True and self.busyTime <= 0:
            priceList = self.setOfPrices
            priceChoice = np.random.choice(priceList, p=self.priceProbs)
            self.priceChoice = priceList.index(priceChoice)
            self.price = priceChoice
            print("Agent {} Choice {}, Index {}".format(self.unique_id,self.price, self.priceChoice))

    def updatePriceProbabilities(self):
        pricePropList = self.pricePropensities
        probs = []
        propSum = sum(pricePropList)
        for index, elem in enumerate(pricePropList):
            elem = elem / propSum
            probs.insert(index, elem)
        self.priceProbs = probs
        print(self.priceProbs)

    def updatePricePropensities(self, reward):
        updated_states = []
        i = 0
        for index, elem in enumerate(self.pricePropensities):
            if index == self.priceChoice:
                print("elem {}".format(elem))
                elem = (1 - self.memory_param) * elem + reward * (1 - self.experimental_param)
            else:
                elem = (1 - self.memory_param) * elem + elem * (self.experimental_param /(len(self.setOfPrices)-1))
            updated_states.insert(index, elem)
            i += 1
        self.pricePropensities = updated_states
        print("Updated price propensities {}".format(self.pricePropensities))

    def setPriceStrategies(self):
        self.setOfPrices = []
        for i in range(50,250,10):
            self.setOfPrices.append(i)

    def setPricePropensities(self):
        self.pricePropensities = []
        for i in range(len(self.setOfPrices)):
            self.pricePropensities.append(1)
        self.initialPropensities = self.pricePropensities
        print("Initial propensities {}".format(self.initialPropensities))

    def setPriceProbabilities(self):
        self.priceProbs = []
        for i in range(len(self.setOfPrices)):
            self.priceProbs.append(1/len(self.setOfPrices))

    def prepareData(self):
        if self.readyToBuy:
            if self.initial_step:
                self.setPriceStrategies()
                self.setPricePropensities()
                self.setPriceProbabilities()
                self.initial_step = False
            print("Set of prices {}".format(self.setOfPrices))
            print("Set of propensities {}".format(self.pricePropensities))
            print("Set of probabilities {}".format(self.priceProbs))

    def checkBusyTime(self):
        if self.busyTime > 0:
            self.status = 'busy'
            self.wantToPark = False
            self.busyTime -= 1
        else:
            self.busyTime = 0
            self.status = 'free'
        print("Busy time {}".format(self.busyTime))

    def getParkingTime(self):
        if not self.wantToPark:
            self.parkingTime = 0
        else:
            self.parkingTime = random.randint(1,5)
        print("Desirable parking time {}".format(self.parkingTime))

    def name_func(self):
        print("Agent {}".format(self.unique_id))

    def checkIfPark(self):
        if self.status == 'free':
            if self.hour >= 7 and self.hour <= 9:
                self.wantToPark = np.random.choice([True, False], p=[0.9, 0.1])
            elif self.hour >= 15 and self.hour <= 17:
                self.wantToPark = np.random.choice([True, False], p=[0.9, 0.1])
            else:
                self.wantToPark = np.random.choice([True, False])
        print("Want to park {}".format(self.wantToPark))

    def getTradeStatus(self):
        if self.wantToPark:
            self.readyToBuy = True
        else:
            self.readyToBuy = False

    def step(self):
        self.name_func()
        self.checkBusyTime()
        self.checkIfPark()
        self.prepareData()
        self.getTradeStatus()
        self.getParkingTime()

        self.hour += 1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0

class ParkingSlotAgent(Agent):
    def __init__(self,unique_id, model):
        super().__init__(unique_id, model)
        self.hour = 0
        self.day = 0
        self.week = 0

        self.status = 'free'
        self.car_id = None
        self.amountOfHours = 0
        self.readyToSell = True
        self.initial_step = True

        self.queue = []

        self.setOfPrices = []
        self.pricePropensities = []
        self.priceProbs = []
        self.initialPropensities = []

        self.currentState = None
        self.memory_param = 0.8
        self.experimental_param = 0.5

        self.price = 0
        self.priceChoice = 0
        self.choice = 0
        self.stateChoice = None

        self.busyTime = 0

    def updateQueue(self):
        if self.status == 'free':
            self.queue = []

    def updatePriceProbabilities(self):
        pricePropList = self.pricePropensities
        probs = []
        propSum = sum(pricePropList)
        for index, elem in enumerate(pricePropList):
            elem = elem / propSum
            probs.insert(index, elem)
        self.priceProbs = probs
        print(self.priceProbs)

    def updatePricePropensities(self, reward):
        updated_states = []
        i = 0
        for index, elem in enumerate(self.pricePropensities):
            if index == self.priceChoice:
                print("elem {}".format(elem))
                elem = (1 - self.memory_param) * elem + (reward * (1 - self.experimental_param))
            else:
                elem = (1 - self.memory_param) * elem + (elem * (self.experimental_param / (len(self.setOfPrices) - 1)))
            updated_states.insert(index, elem)
            i += 1
        self.pricePropensities = updated_states
        print("Updated price propensities {}".format(self.pricePropensities))


    def updateCriticalPropensities(self):
        print("Propensity update")
        for index,elem in enumerate(self.pricePropensities):
            self.pricePropensities[index] = round(elem * 0.9, 3)
            self.pricePropensities[index] = elem + 0.1

    def prepareData(self):
        if self.readyToSell:
            if self.initial_step:
                self.setPriceStrategies()
                self.setPricePropensities()
                self.setPriceProbabilities()
                self.initial_step = False
            print("Set of prices {}".format(self.setOfPrices))
            print("Set of propensities {}".format(self.pricePropensities))
            print("Set of probabilities {}".format(self.priceProbs))

    def setPriceStrategies(self):
        self.setOfPrices = []
        for i in range(50,250,10):
            self.setOfPrices.append(i)

    def setPricePropensities(self):
        self.pricePropensities = []
        for i in range(len(self.setOfPrices)):
            self.pricePropensities.append(1)
        self.initialPropensities = self.pricePropensities
        print("Initial propensities {}".format(self.initialPropensities))

    def setPriceProbabilities(self):
        self.priceProbs = []
        for i in range(len(self.setOfPrices)):
            self.priceProbs.append(1/len(self.setOfPrices))

    def choosePrice(self):
        if self.readyToSell is True:
            priceList = self.setOfPrices
            priceChoice = np.random.choice(priceList, p=self.priceProbs)
            self.priceChoice = priceList.index(priceChoice)
            self.price = priceChoice
            print("Agent {} Choice {}, Index {}".format(self.unique_id,priceChoice, self.priceChoice))

    def checkBusyTime(self):
        if self.busyTime > 0:
            self.status = 'busy'
            self.readyToSell = False
            self.busyTime -= 1
        else:
            self.busyTime = 0
            self.status = 'free'
        print("Busy time {}".format(self.busyTime))
        print("Busy status {}".format(self.status))


    def getSellStatus(self):
        if self.status == 'free':
            self.readyToSell = True
        else:
            self.readyToSell = False

    def getStatus(self):
        self.status = random.choice(['free','busy'])
        print(self.status)

    def name_func(self):
        print("Agent {}".format(self.unique_id))

    def step(self):
        self.name_func()
        self.checkBusyTime()
        self.updateQueue()
        self.getSellStatus()

        self.prepareData()
        self.choosePrice()

        self.hour += 1

        if self.hour > 23:
            self.day += 1
            self.hour = 0

        if self.day > 7:
            self.week += 1
            self.day = 0