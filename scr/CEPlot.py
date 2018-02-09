import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


class Strategy:
    def __init__(self, name, cost, effect):
        """        
        :param name: name of the strategy
        :param cost: list o numpy.array  
        :param effect: list or numpy.array
        """
        self.name = name
        self.cost = cost
        self.effect = effect
        self.aveCost = np.average(self.cost)
        self.aveEffect = np.average(self.effect)
        self.ifDominated = False


class CEA:
    def __init__(self, strategies):
        """
        :param strategies: the list of strategies
        """
        self.n = len(strategies)
        self.strategiesOnFrontier = pd.DataFrame()  # data frame to contain the strategies on the frontier
        
        self.dfStrategies = pd.DataFrame(
            index=range(self.n), 
            columns=['Name', 'E[Cost]', 'E[Effect]', 'Dominated', 'Color'])

        for i in range(len(strategies)):
            self.dfStrategies.loc[i, 'Name'] = strategies[i].name
            self.dfStrategies.loc[i, 'E[Cost]'] = strategies[i].aveCost
            self.dfStrategies.loc[i, 'E[Effect]'] = strategies[i].aveEffect
            self.dfStrategies.loc[i, 'Dominated'] = strategies[i].ifDominated
            self.dfStrategies.loc[i, 'Color'] = "k"  # not Dominated black, Dominated blue

        # find the CE frontier
        self.find_frontier()

    def get_frontier(self):
        return self.strategiesOnFrontier

    def find_frontier(self):
        # sort strategies by cost, ascending
        # operate on local variable data rather than self attribute
        df1 = self.dfStrategies.sort_values('E[Cost]')

        # apply criteria 1
        for i in range(self.n):
            # strategies with higher cost and lower Effect are dominated
            df1.loc[
                (df1['E[Cost]'] > df1['E[Cost]'][i]) &
                (df1['E[Effect]'] <= df1['E[Effect]'][i]),
                'Dominated'] = True
        # change the color of dominated strategies to blue
        df1.loc[df1['Dominated'] == True, 'Color'] = 'blue'

        # apply criteria 2
        # select all non-dominated strategies
        df2 = df1.loc[df1['Dominated']==False]
        n2 = len(df2['E[Cost]'])

        for i in range(0, n2): # can't decide for first and last point
            for j in range(i+1, n2):
                # cost and effect of strategy i
                effect_i = df2['E[Effect]'].iloc[i]
                cost_i = df2['E[Cost]'].iloc[i]
                # cost and effect of strategy j
                effect_j = df2['E[Effect]'].iloc[j]
                cost_j = df2['E[Cost]'].iloc[j]
                # vector connecting strategy i to j
                v_i_to_j = np.array([effect_j-effect_i, cost_j-cost_i])

                # if the effect of no strategy is between the effects of strategies i and j
                if not ((df2['E[Effect]'] > effect_i) & (df2['E[Effect]'] < effect_j)).any():
                    continue    # to the next j
                else:
                    # get all the strategies with effect between strategies i and j
                    inner_points = df2.loc[(df2['E[Effect]'] > effect_i) & (df2['E[Effect]'] < effect_j)]
                    # difference in effect of inner points and strategy i
                    v2_x = inner_points['E[Effect]'] - effect_i
                    # difference in cost of inner points and strategy i
                    v2_y = inner_points['E[Cost]']-cost_i

                    # cross products of vector i to j and the vectors i to all inner points
                    cross_product = v_i_to_j[0] * np.array(v2_y) - v_i_to_j[1] * np.array(v2_x)

                    # if cross_product > 0 the point is above the line
                    # (because the point are sorted vertically)
                    # ref: https://stackoverflow.com/questions/1560492/how-to-tell-whether-a-point-is-to-the-right-or-left-side-of-a-line
                    dominated_index = inner_points[cross_product > 0].index
                    df1.loc[list(dominated_index), 'Dominated'] = True
                    df1.loc[list(dominated_index), 'Color'] = 'blue'

        # update strategies
        self.dfStrategies = df1
        self.strategiesOnFrontier = df1.loc[df1['Dominated']==False, ['Name', 'E[Cost]', 'E[Effect]']]

    def show_CE_plane(self, show_names = False):
        # plots
        # operate on local variable data rather than self attribute
        data = self.dfStrategies

        # re-sorted according to Effect to draw line
        linedat = data.loc[data["Dominated"] == False].sort_values('E[Effect]')

        plt.scatter(data['E[Effect]'], data['E[Cost]'], c=list(data['Color']))
        plt.plot(linedat['E[Effect]'], linedat['E[Cost]'], c='k')
        plt.axhline(y=0, Color='k',linewidth=0.5)
        plt.axvline(x=0, Color='k',linewidth=0.5)
        plt.xlabel('E[Effect]')
        plt.ylabel('E[Cost]')
        plt.show()


    def BuildCETable(self):
        data = self.dfStrategies
        data['Expected Incremental Cost'] = "-"
        data['Expected Incremental Effect'] = "-"
        data['ICER'] = "Dominated"
        not_Dominated_points = data.loc[data["Dominated"] == False].sort_values('E[Cost]')

        n_not_Dominated = not_Dominated_points.shape[0]


        incre_cost = []
        incre_Effect = []
        ICER = []
        for i in range(1, n_not_Dominated):
            temp_num = not_Dominated_points["E[Cost]"].iloc[i]-not_Dominated_points["E[Cost]"].iloc[i-1]
            incre_cost = np.append(incre_cost, temp_num)

            temp_den = not_Dominated_points["E[Effect]"].iloc[i]-not_Dominated_points["E[Effect]"].iloc[i-1]
            if temp_den == 0:
                raise ValueError('invalid value of Expected Incremental Effect, the ratio is not computable')
            incre_Effect = np.append(incre_Effect, temp_den)

            ICER = np.append(ICER, temp_num/temp_den)

        ind_change = not_Dominated_points.index[1:]
        data.loc[ind_change, 'Expected Incremental Cost'] = incre_cost
        data.loc[ind_change, 'Expected Incremental Effect'] = incre_Effect
        data.loc[ind_change, 'ICER'] = ICER
        data.loc[not_Dominated_points.index[0], 'ICER'] = '-'

        return data[['Name', 'E[Cost]', 'E[Effect]', 'Expected Incremental Cost', 'Expected Incremental Effect',\
            'ICER']]


np.random.seed(573)

s0 = Strategy('s0',0, 0)
s1 = Strategy("s1",np.random.normal(0, 5),np.random.normal(0, 5))
s2 = Strategy("s2",np.random.normal(0, 5),np.random.normal(0, 5))
s3 = Strategy("s3",np.random.normal(0, 5),np.random.normal(0, 5))
s4 = Strategy("s4",np.random.normal(0, 5),np.random.normal(0, 5))
s5 = Strategy("s5",np.random.normal(0, 5),np.random.normal(0, 5))
s6 = Strategy("s6",np.random.normal(0, 5),np.random.normal(0, 5))
s7 = Strategy("s7",np.random.normal(0, 5),np.random.normal(0, 5))
s8 = Strategy("s8",np.random.normal(0, 5),np.random.normal(0, 5))
s9 = Strategy("s9",np.random.normal(0, 5),np.random.normal(0, 5))
s10 = Strategy("s10",np.random.normal(0, 5),np.random.normal(0, 5))


strategies = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]
myCEA = CEA(strategies)

# frontier results
frontiers = myCEA.get_frontier()
print(frontiers)


# updated strategies
myCEA.dfStrategies

# plot
myCEA.show_CE_plane()

