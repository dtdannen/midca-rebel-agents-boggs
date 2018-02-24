import csv
from matplotlib import pyplot as plt
import numpy as np
from statistics import mean
from scipy.interpolate import griddata
import sqlite3
from copy import copy

dFile = open('testRecords.csv', 'r')
dReader = csv.DictReader(dFile)
dDict = dict()

# for row in dReader:
#     for fName in dReader.fieldnames:
#         if fName not in dDict:
#             dDict[fName] = [eval(row[fName])]
#         else:
#             dDict[fName].append(eval(row[fName]))
#
# dDict['agentMean'] = [mean(data) for data in dDict['agents']]
# dDict['optrMean'] = [mean(data) for data in dDict['operators']]
# dDict['density'] = [(dDict['civilians'][i] + dDict['enemies'][i])/float(dDict['worldSize'][i]**2) for i in range(len(dDict['enemies']))]
#
# conn = sqlite3.connect('results.db')
# c = conn.cursor()
# c.execute('''CREATE TABLE data
#              (worldSize integer, civilians integer, enemies integer, density real, enemiesKilled real, civsLiving real, agentMean real, optrMean real)''')
# for i in range(len(dDict['worldSize'])):
#     c.execute('''INSERT INTO data VALUES
#               ({wSize}, {civs}, {enemies}, {dens}, {ek}, {cl}, {agtMean}, {optrmean})'''.format(wSize = dDict['worldSize'][i],
#                                                                                                 civs = dDict['civilians'][i],
#                                                                                                 enemies = dDict['enemies'][i],
#                                                                                                 dens = dDict['density'][i],
#                                                                                                 ek = dDict['Enemies Killed'][i],
#                                                                                                 cl = dDict['Civilians Living'][i],
#                                                                                                 agtMean = dDict['agentMean'][i],
#                                                                                                 optrmean = dDict['optrMean'][i]))
# conn.commit()
# conn.close()

### HEATMAP CREATION
conn = sqlite3.connect('results.db')
c = conn.cursor()

## TOTAL HEATMAPS
# agentVals = []
# optrVals = []
# killVals = []
# liveVals = []
# plt.figure(1)
#
# for row in c.execute('SELECT agentMean, optrMean, enemiesKilled, civsLiving FROM data'):
#     agentVals.append(row[0])
#     optrVals.append(row[1])
#     killVals.append(row[2])
#     liveVals.append(row[3])
#
# agentVals = np.array(agentVals)
# optrVals = np.array(optrVals)
# killVals = np.array(killVals)
# liveVals = np.array(liveVals)
#
#
# agentLocs = np.linspace(min(agentVals), max(agentVals), len(set(agentVals)))
# optrLocs = np.linspace(min(optrVals), max(optrVals), len(set(optrVals)))
# killGrid = griddata((agentVals, optrVals),
#                     killVals,
#                     (agentLocs[None,:], optrLocs[:,None]),
#                     method='linear'
#                     )
# liveGrid = griddata((agentVals, optrVals),
#                     liveVals,
#                     (agentLocs[None,:], optrLocs[:,None]),
#                     method='linear'
#                     )
#
# plt.subplot(2,4,1)
# killContPlot = plt.contourf(agentLocs, optrLocs, killGrid, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Enemies Killed')
# plt.colorbar(mappable=killContPlot)
#
# plt.subplot(2,4,2)
# liveContPlot = plt.contourf(agentLocs, optrLocs, liveGrid, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Civs Surviving')
# plt.colorbar()
#
#
# ## LOW DENSITY HEATMAPS
# agentValsLo = []
# optrValsLo = []
# killValsLo = []
# liveValsLo = []
#
# for row in c.execute('SELECT agentMean, optrMean, enemiesKilled, civsLiving FROM data WHERE density=0.1'):
#     agentValsLo.append(row[0])
#     optrValsLo.append(row[1])
#     killValsLo.append(row[2])
#     liveValsLo.append(row[3])
#
# agentValsLo = np.array(agentValsLo)
# optrValsLo = np.array(optrValsLo)
# killValsLo = np.array(killValsLo)
# liveValsLo = np.array(liveValsLo)
#
#
# agentLocsLo = np.linspace(min(agentValsLo), max(agentValsLo), len(set(agentValsLo)))
# optrLocsLo = np.linspace(min(optrValsLo), max(optrValsLo), len(set(optrValsLo)))
# killGridLo = griddata((agentValsLo, optrValsLo),
#                     killValsLo,
#                     (agentLocsLo[None,:], optrLocsLo[:,None]),
#                     method='linear'
#                     )
# liveGridLo = griddata((agentValsLo, optrValsLo),
#                     liveValsLo,
#                     (agentLocsLo[None,:], optrLocsLo[:,None]),
#                     method='linear'
#                     )
#
# plt.subplot(2,4,3)
# killContPlotLo = plt.contourf(agentLocsLo, optrLocsLo, killGridLo, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Enemies Killed (Low-Density)')
# plt.colorbar(mappable=killContPlotLo)
#
# plt.subplot(2,4,4)
# liveContPlotLo = plt.contourf(agentLocsLo, optrLocsLo, liveGridLo, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Civs Surviving (Low-Density)')
# plt.colorbar()
#
# ## MEDIUM DENSITY HEATMAPS
# agentValsMed = []
# optrValsMed = []
# killValsMed = []
# liveValsMed = []
#
# for row in c.execute('SELECT agentMean, optrMean, enemiesKilled, civsLiving FROM data WHERE density=0.2'):
#     agentValsMed.append(row[0])
#     optrValsMed.append(row[1])
#     killValsMed.append(row[2])
#     liveValsMed.append(row[3])
#
# agentValsMed = np.array(agentValsMed)
# optrValsMed = np.array(optrValsMed)
# killValsMed = np.array(killValsMed)
# liveValsMed = np.array(liveValsMed)
#
#
# agentLocsMed = np.linspace(min(agentValsMed), max(agentValsMed), len(set(agentValsMed)))
# optrLocsMed = np.linspace(min(optrValsMed), max(optrValsMed), len(set(optrValsMed)))
# killGridMed = griddata((agentValsMed, optrValsMed),
#                     killValsMed,
#                     (agentLocsMed[None,:], optrLocsMed[:,None]),
#                     method='linear'
#                     )
# liveGridMed = griddata((agentValsMed, optrValsMed),
#                     liveValsMed,
#                     (agentLocsMed[None,:], optrLocsMed[:,None]),
#                     method='linear'
#                     )
#
# plt.subplot(2,4,5)
# killContPlotMed = plt.contourf(agentLocsMed, optrLocsMed, killGridMed, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Enemies Killed (Med-Density)')
# plt.colorbar(mappable=killContPlotMed)
#
# plt.subplot(2,4,6)
# liveContPlotMed = plt.contourf(agentLocsMed, optrLocsMed, liveGridMed, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Civs Surviving (Med-Density)')
# plt.colorbar()
#
# ## HIGH DENSITY HEATMAPS
# agentValsHi = []
# optrValsHi = []
# killValsHi = []
# liveValsHi = []
#
# for row in c.execute('SELECT agentMean, optrMean, enemiesKilled, civsLiving FROM data WHERE density=0.4'):
#     agentValsHi.append(row[0])
#     optrValsHi.append(row[1])
#     killValsHi.append(row[2])
#     liveValsHi.append(row[3])
#
# agentValsHi = np.array(agentValsHi)
# optrValsHi = np.array(optrValsHi)
# killValsHi = np.array(killValsHi)
# liveValsHi = np.array(liveValsHi)
#
#
# agentLocsHi = np.linspace(min(agentValsHi), max(agentValsHi), len(set(agentValsHi)))
# optrLocsHi = np.linspace(min(optrValsHi), max(optrValsHi), len(set(optrValsHi)))
# killGridHi = griddata((agentValsHi, optrValsHi),
#                     killValsHi,
#                     (agentLocsHi[None,:], optrLocsHi[:,None]),
#                     method='cubic'
#                     )
# liveGridHi = griddata((agentValsHi, optrValsHi),
#                     liveValsHi,
#                     (agentLocsHi[None,:], optrLocsHi[:,None]),
#                     method='cubic'
#                     )
#
# plt.subplot(2,4,7)
# killContPlotHi = plt.contourf(agentLocsHi, optrLocsHi, killGridHi, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Enemies Killed (High-Density Maps)')
# plt.colorbar(mappable=killContPlotHi)
#
# plt.subplot(2,4,8)
# liveContPlotHi = plt.contourf(agentLocsHi, optrLocsHi, liveGridHi, levels=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], cmap='hot')
# plt.xlabel('Agent Compliance')
# plt.ylabel('Operator Resolve')
# plt.title('% of Civs Surviving (High-Density)')
# plt.colorbar()
# plt.show()
#
#
# ### SCATTERPLOTS OF ENEMIES KILLED
# ## AGENT VALUES
# plt.figure(2)
# # TOTAL
# agentScatDataDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatData = []
# killScatData = []
# for row in c.execute('SELECT agentMean, enemiesKilled FROM data'):
#     agentScatDataDict[row[0]].append(row[1])
#     agentScatData.append(row[0])
#     killScatData.append(row[1])
# agtAvgX = agentScatDataDict.keys()
# agtAvgX.sort()
# agtAvgY = [mean(agentScatDataDict[aVal]) for aVal in agtAvgX]
# plt.subplot(2,2,1)
# plt.plot(agentScatData, killScatData, 'ro', agtAvgX, agtAvgY, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Agent Compliance')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # LOW-DENSITY
# agentScatDataDictLo = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatDataLo = []
# killScatDataLo = []
# for row in c.execute('SELECT agentMean, enemiesKilled FROM data WHERE density=0.1'):
#     agentScatDataDictLo[row[0]].append(row[1])
#     agentScatDataLo.append(row[0])
#     killScatDataLo.append(row[1])
# agtAvgXLo = agentScatDataDictLo.keys()
# agtAvgXLo.sort()
# agtAvgYLo = [mean(agentScatDataDictLo[aVal]) for aVal in agtAvgXLo]
# plt.subplot(2,2,2)
# plt.plot(agentScatDataLo, killScatDataLo, 'ro', agtAvgXLo, agtAvgYLo, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Agent Compliance (Low-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # MED-DENSITY
# agentScatDataDictMed = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatDataMed = []
# killScatDataMed = []
# for row in c.execute('SELECT agentMean, enemiesKilled FROM data WHERE density=0.2'):
#     agentScatDataDictMed[row[0]].append(row[1])
#     agentScatDataMed.append(row[0])
#     killScatDataMed.append(row[1])
# agtAvgXMed = agentScatDataDictMed.keys()
# agtAvgXMed.sort()
# agtAvgYMed = [mean(agentScatDataDictMed[aVal]) for aVal in agtAvgXMed]
# plt.subplot(2,2,3)
# plt.plot(agentScatDataMed, killScatDataMed, 'ro', agtAvgXMed, agtAvgYMed, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Agent Compliance (Med-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# #HIGH-DENSITY
# agentScatDataDictHi = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatDataHi = []
# killScatDataHi = []
# for row in c.execute('SELECT agentMean, enemiesKilled FROM data WHERE density=0.4'):
#     agentScatDataDictHi[row[0]].append(row[1])
#     agentScatDataHi.append(row[0])
#     killScatDataHi.append(row[1])
# agtAvgXHi = agentScatDataDictHi.keys()
# agtAvgXHi.sort()
# agtAvgYHi = [mean(agentScatDataDictHi[aVal]) for aVal in agtAvgXHi]
# plt.subplot(2,2,4)
# plt.plot(agentScatDataHi, killScatDataHi, 'ro', agtAvgXHi, agtAvgYHi, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Agent Compliance (High-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
# plt.show()
#
# ## OPERATOR VALUES VS ENEMY DEATHS
# plt.figure(3)
# # TOTAL
# optrScatDataDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatData = []
# killScatData = []
# for row in c.execute('SELECT optrMean, enemiesKilled FROM data'):
#     optrScatDataDict[row[0]].append(row[1])
#     optrScatData.append(row[0])
#     killScatData.append(row[1])
# agtAvgX = optrScatDataDict.keys()
# agtAvgX.sort()
# agtAvgY = [mean(optrScatDataDict[aVal]) for aVal in agtAvgX]
# plt.subplot(2,2,1)
# plt.plot(optrScatData, killScatData, 'ro', agtAvgX, agtAvgY, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Operator Resolve')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # LOW-DENSITY
# optrScatDataDictLo = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataLo = []
# killScatDataLo = []
# for row in c.execute('SELECT optrMean, enemiesKilled FROM data WHERE density=0.1'):
#     optrScatDataDictLo[row[0]].append(row[1])
#     optrScatDataLo.append(row[0])
#     killScatDataLo.append(row[1])
# agtAvgXLo = optrScatDataDictLo.keys()
# agtAvgXLo.sort()
# agtAvgYLo = [mean(optrScatDataDictLo[aVal]) for aVal in agtAvgXLo]
# plt.subplot(2,2,2)
# plt.plot(optrScatDataLo, killScatDataLo, 'ro', agtAvgXLo, agtAvgYLo, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Operator Resolve (Low-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # MED-DENSITY
# optrScatDataDictMed = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataMed = []
# killScatDataMed = []
# for row in c.execute('SELECT optrMean, enemiesKilled FROM data WHERE density=0.2'):
#     optrScatDataDictMed[row[0]].append(row[1])
#     optrScatDataMed.append(row[0])
#     killScatDataMed.append(row[1])
# agtAvgXMed = optrScatDataDictMed.keys()
# agtAvgXMed.sort()
# agtAvgYMed = [mean(optrScatDataDictMed[aVal]) for aVal in agtAvgXMed]
# plt.subplot(2,2,3)
# plt.plot(optrScatDataMed, killScatDataMed, 'ro', agtAvgXMed, agtAvgYMed, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Operator Resolve (Med-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# #HIGH-DENSITY
# optrScatDataDictHi = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataHi = []
# killScatDataHi = []
# for row in c.execute('SELECT optrMean, enemiesKilled FROM data WHERE density=0.4'):
#     optrScatDataDictHi[row[0]].append(row[1])
#     optrScatDataHi.append(row[0])
#     killScatDataHi.append(row[1])
# agtAvgXHi = optrScatDataDictHi.keys()
# agtAvgXHi.sort()
# agtAvgYHi = [mean(optrScatDataDictHi[aVal]) for aVal in agtAvgXHi]
# plt.subplot(2,2,4)
# plt.plot(optrScatDataHi, killScatDataHi, 'ro', agtAvgXHi, agtAvgYHi, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Enemies Killed')
# plt.title('% Enemies Killed vs. Operator Resolve (High-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
# plt.show()
#
# ### SCATTERPLOTS OF CIVILIANS ALIVE
# ## AGENT VALUES
# plt.figure(4)
# # TOTAL
# agentScatDataDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatData = []
# liveScatData = []
# for row in c.execute('SELECT agentMean, civsLiving FROM data'):
#     agentScatDataDict[row[0]].append(row[1])
#     agentScatData.append(row[0])
#     liveScatData.append(row[1])
# agtAvgX = agentScatDataDict.keys()
# agtAvgX.sort()
# agtAvgY = [mean(agentScatDataDict[aVal]) for aVal in agtAvgX]
# plt.subplot(2,2,1)
# plt.plot(agentScatData, liveScatData, 'ro', agtAvgX, agtAvgY, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Agent Compliance')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # LOW-DENSITY
# agentScatDataDictLo = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatDataLo = []
# liveScatDataLo = []
# for row in c.execute('SELECT agentMean, civsLiving FROM data WHERE density=0.1'):
#     agentScatDataDictLo[row[0]].append(row[1])
#     agentScatDataLo.append(row[0])
#     liveScatDataLo.append(row[1])
# agtAvgXLo = agentScatDataDictLo.keys()
# agtAvgXLo.sort()
# agtAvgYLo = [mean(agentScatDataDictLo[aVal]) for aVal in agtAvgXLo]
# plt.subplot(2,2,2)
# plt.plot(agentScatDataLo, liveScatDataLo, 'ro', agtAvgXLo, agtAvgYLo, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Agent Compliance (Low-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # MED-DENSITY
# agentScatDataDictMed = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatDataMed = []
# liveScatDataMed = []
# for row in c.execute('SELECT agentMean, civsLiving FROM data WHERE density=0.2'):
#     agentScatDataDictMed[row[0]].append(row[1])
#     agentScatDataMed.append(row[0])
#     liveScatDataMed.append(row[1])
# agtAvgXMed = agentScatDataDictMed.keys()
# agtAvgXMed.sort()
# agtAvgYMed = [mean(agentScatDataDictMed[aVal]) for aVal in agtAvgXMed]
# plt.subplot(2,2,3)
# plt.plot(agentScatDataMed, liveScatDataMed, 'ro', agtAvgXMed, agtAvgYMed, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Agent Compliance (Med-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# #HIGH-DENSITY
# agentScatDataDictHi = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# agentScatDataHi = []
# liveScatDataHi = []
# for row in c.execute('SELECT agentMean, civsLiving FROM data WHERE density=0.4'):
#     agentScatDataDictHi[row[0]].append(row[1])
#     agentScatDataHi.append(row[0])
#     liveScatDataHi.append(row[1])
# agtAvgXHi = agentScatDataDictHi.keys()
# agtAvgXHi.sort()
# agtAvgYHi = [mean(agentScatDataDictHi[aVal]) for aVal in agtAvgXHi]
# plt.subplot(2,2,4)
# plt.plot(agentScatDataHi, liveScatDataHi, 'ro', agtAvgXHi, agtAvgYHi, 'b--')
# plt.xlabel('Agent Compliance')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Agent Compliance (High-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
# plt.show()
#
# ## OPERATOR VALUES
# plt.figure(5)
# # TOTAL
# optrScatDataDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatData = []
# liveScatData = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data'):
#     optrScatDataDict[row[0]].append(row[1])
#     optrScatData.append(row[0])
#     liveScatData.append(row[1])
# agtAvgX = optrScatDataDict.keys()
# agtAvgX.sort()
# agtAvgY = [mean(optrScatDataDict[aVal]) for aVal in agtAvgX]
# plt.subplot(2,2,1)
# plt.plot(optrScatData, liveScatData, 'ro', agtAvgX, agtAvgY, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # LOW-DENSITY
# optrScatDataDictLo = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataLo = []
# liveScatDataLo = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data WHERE density=0.1'):
#     optrScatDataDictLo[row[0]].append(row[1])
#     optrScatDataLo.append(row[0])
#     liveScatDataLo.append(row[1])
# agtAvgXLo = optrScatDataDictLo.keys()
# agtAvgXLo.sort()
# agtAvgYLo = [mean(optrScatDataDictLo[aVal]) for aVal in agtAvgXLo]
# plt.subplot(2,2,2)
# plt.plot(optrScatDataLo, liveScatDataLo, 'ro', agtAvgXLo, agtAvgYLo, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve (Low-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # MED-DENSITY
# optrScatDataDictMed = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataMed = []
# liveScatDataMed = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data WHERE density=0.2'):
#     optrScatDataDictMed[row[0]].append(row[1])
#     optrScatDataMed.append(row[0])
#     liveScatDataMed.append(row[1])
# agtAvgXMed = optrScatDataDictMed.keys()
# agtAvgXMed.sort()
# agtAvgYMed = [mean(optrScatDataDictMed[aVal]) for aVal in agtAvgXMed]
# plt.subplot(2,2,3)
# plt.plot(optrScatDataMed, liveScatDataMed, 'ro', agtAvgXMed, agtAvgYMed, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve (Med-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# #HIGH-DENSITY
# optrScatDataDictHi = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataHi = []
# liveScatDataHi = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data WHERE density=0.4'):
#     optrScatDataDictHi[row[0]].append(row[1])
#     optrScatDataHi.append(row[0])
#     liveScatDataHi.append(row[1])
# agtAvgXHi = optrScatDataDictHi.keys()
# agtAvgXHi.sort()
# agtAvgYHi = [mean(optrScatDataDictHi[aVal]) for aVal in agtAvgXHi]
# plt.subplot(2,2,4)
# plt.plot(optrScatDataHi, liveScatDataHi, 'ro', agtAvgXHi, agtAvgYHi, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve (High-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
# plt.show()
#
# plt.figure(6)
# # TOTAL
# optrScatDataDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatData = []
# liveScatData = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data'):
#     optrScatDataDict[row[0]].append(row[1])
#     optrScatData.append(row[0])
#     liveScatData.append(row[1])
# agtAvgX = optrScatDataDict.keys()
# agtAvgX.sort()
# agtAvgY = [mean(optrScatDataDict[aVal]) for aVal in agtAvgX]
# plt.subplot(2,2,1)
# plt.plot(optrScatData, liveScatData, 'ro', agtAvgX, agtAvgY, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # LOW-DENSITY
# optrScatDataDictLo = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataLo = []
# liveScatDataLo = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data WHERE density=0.1'):
#     optrScatDataDictLo[row[0]].append(row[1])
#     optrScatDataLo.append(row[0])
#     liveScatDataLo.append(row[1])
# agtAvgXLo = optrScatDataDictLo.keys()
# agtAvgXLo.sort()
# agtAvgYLo = [mean(optrScatDataDictLo[aVal]) for aVal in agtAvgXLo]
# plt.subplot(2,2,2)
# plt.plot(optrScatDataLo, liveScatDataLo, 'ro', agtAvgXLo, agtAvgYLo, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve (Low-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# # MED-DENSITY
# optrScatDataDictMed = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataMed = []
# liveScatDataMed = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data WHERE density=0.2'):
#     optrScatDataDictMed[row[0]].append(row[1])
#     optrScatDataMed.append(row[0])
#     liveScatDataMed.append(row[1])
# agtAvgXMed = optrScatDataDictMed.keys()
# agtAvgXMed.sort()
# agtAvgYMed = [mean(optrScatDataDictMed[aVal]) for aVal in agtAvgXMed]
# plt.subplot(2,2,3)
# plt.plot(optrScatDataMed, liveScatDataMed, 'ro', agtAvgXMed, agtAvgYMed, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve (Med-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
#
# #HIGH-DENSITY
# optrScatDataDictHi = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
# optrScatDataHi = []
# liveScatDataHi = []
# for row in c.execute('SELECT optrMean, civsLiving FROM data WHERE density=0.4'):
#     optrScatDataDictHi[row[0]].append(row[1])
#     optrScatDataHi.append(row[0])
#     liveScatDataHi.append(row[1])
# agtAvgXHi = optrScatDataDictHi.keys()
# agtAvgXHi.sort()
# agtAvgYHi = [mean(optrScatDataDictHi[aVal]) for aVal in agtAvgXHi]
# plt.subplot(2,2,4)
# plt.plot(optrScatDataHi, liveScatDataHi, 'ro', agtAvgXHi, agtAvgYHi, 'b--')
# plt.xlabel('Operator Resolve')
# plt.ylabel('% Civs Alive')
# plt.title('% Civs Alive vs. Operator Resolve (High-Density)')
# plt.axis([0.0, 1.0, 0.0, 1.0])
# plt.show()

# ENEMY KILLS AND CIVILIAN LIVES AGAINST OPERATOR RESOLVE
killsLivesvsOptr, axes = plt.subplots(2, 2, num='ENEMY KILLS AND CIVILIAN LIVES AGAINST OPERATOR RESOLVE')
allDens = axes[0,0]
lDens =  axes[0,1]
mDens =  axes[1,0]
hDens =  axes[1,1]
## TOTAL
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT optrMean, enemiesKilled, civsLiving FROM data'):
    optrMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[optrMean].append(enemiesKilled)
    civsLivingDict[optrMean].append(civsLiving)
optrMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[optrMean]) for optrMean in optrMeans]
civsLivingMeans = [mean(civsLivingDict[optrMean]) for optrMean in optrMeans]
allDens.plot(optrMeans, civsLivingMeans, 'b--')
allDens.set_xlabel('Operator Resolve')
allDens.set_ylabel('% Civilians Alive', color='b')
allDens.tick_params('y', colors='b')

allDens2 = allDens.twinx()
allDens2.plot(optrMeans, enemiesKilledMeans, 'r--')
allDens2.set_ylabel('% Enemies Killed', color='r')
allDens2.tick_params('y', colors='r')
allDens.set_title('Total Results')
allDens.axis([0.0, 1.0, 0.0, 1.0])
allDens2.axis([0.0, 1.0, 0.0, 1.0])

## LOW-DENSITY
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT optrMean, enemiesKilled, civsLiving FROM data WHERE density=0.1'):
    optrMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[optrMean].append(enemiesKilled)
    civsLivingDict[optrMean].append(civsLiving)
optrMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[optrMean]) for optrMean in optrMeans]
civsLivingMeans = [mean(civsLivingDict[optrMean]) for optrMean in optrMeans]
lDens.plot(optrMeans, civsLivingMeans, 'b--')
lDens.set_xlabel('Operator Resolve')
lDens.set_ylabel('% Civilians Alive', color='b')
lDens.tick_params('y', colors='b')

lDens2 = lDens.twinx()
lDens2.plot(optrMeans, enemiesKilledMeans, 'r--')
lDens2.set_ylabel('% Enemies Killed', color='r')
lDens2.tick_params('y', colors='r')
lDens.set_title('Total Results')
lDens.axis([0.0, 1.0, 0.0, 1.0])
lDens2.axis([0.0, 1.0, 0.0, 1.0])

# ## MED-DENSITY
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT optrMean, enemiesKilled, civsLiving FROM data WHERE density=0.2'):
    optrMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[optrMean].append(enemiesKilled)
    civsLivingDict[optrMean].append(civsLiving)
optrMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[optrMean]) for optrMean in optrMeans]
civsLivingMeans = [mean(civsLivingDict[optrMean]) for optrMean in optrMeans]
mDens.plot(optrMeans, civsLivingMeans, 'b--')
mDens.set_xlabel('Operator Resolve')
mDens.set_ylabel('% Civilians Alive', color='b')
mDens.tick_params('y', colors='b')

mDens2 = mDens.twinx()
mDens2.plot(optrMeans, enemiesKilledMeans, 'r--')
mDens2.set_ylabel('% Enemies Killed', color='r')
mDens2.tick_params('y', colors='r')
mDens.set_title('Total Results')
mDens.axis([0.0, 1.0, 0.0, 1.0])
mDens2.axis([0.0, 1.0, 0.0, 1.0])

# #HIGH-DENSITY
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT optrMean, enemiesKilled, civsLiving FROM data WHERE density=0.4'):
    optrMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[optrMean].append(enemiesKilled)
    civsLivingDict[optrMean].append(civsLiving)
optrMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[optrMean]) for optrMean in optrMeans]
civsLivingMeans = [mean(civsLivingDict[optrMean]) for optrMean in optrMeans]
hDens.plot(optrMeans, civsLivingMeans, 'b--')
hDens.set_xlabel('Operator Resolve')
hDens.set_ylabel('% Civilians Alive', color='b')
hDens.tick_params('y', colors='b')

hDens2 = hDens.twinx()
hDens2.plot(optrMeans, enemiesKilledMeans, 'r--')
hDens2.set_ylabel('% Enemies Killed', color='r')
hDens2.tick_params('y', colors='r')
hDens.set_title('Total Results')
hDens.axis([0.0, 1.0, 0.0, 1.0])
hDens2.axis([0.0, 1.0, 0.0, 1.0])

killsLivesvsOptr.tight_layout()


# ENEMIES KILLED AND CIVILIANS ALIVE VS AGENT COMPLIANCE
killsLivesvsAgt, axes = plt.subplots(2, 2, num='ENEMY KILLS AND CIVILIAN LIVES AGAINST AGENT COMPLIANCE')
allDens = axes[0,0]
lDens =  axes[0,1]
mDens =  axes[1,0]
hDens =  axes[1,1]
## TOTAL
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT agentMean, enemiesKilled, civsLiving FROM data'):
    agentMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[agentMean].append(enemiesKilled)
    civsLivingDict[agentMean].append(civsLiving)
agentMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[agentMean]) for agentMean in agentMeans]
civsLivingMeans = [mean(civsLivingDict[agentMean]) for agentMean in agentMeans]
allDens.plot(agentMeans, civsLivingMeans, 'b--')
allDens.set_xlabel('Agent Compliance')
allDens.set_ylabel('% Civilians Alive', color='b')
allDens.tick_params('y', colors='b')

allDens2 = allDens.twinx()
allDens2.plot(agentMeans, enemiesKilledMeans, 'r--')
allDens2.set_ylabel('% Enemies Killed', color='r')
allDens2.tick_params('y', colors='r')
allDens.set_title('Total Results')
allDens.axis([0.0, 1.0, 0.0, 1.0])
allDens2.axis([0.0, 1.0, 0.0, 1.0])

## LOW-DENSITY
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT agentMean, enemiesKilled, civsLiving FROM data WHERE density=0.1'):
    agentMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[agentMean].append(enemiesKilled)
    civsLivingDict[agentMean].append(civsLiving)
agentMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[agentMean]) for agentMean in agentMeans]
civsLivingMeans = [mean(civsLivingDict[agentMean]) for agentMean in agentMeans]
lDens.plot(agentMeans, civsLivingMeans, 'b--')
lDens.set_xlabel('Agent Compliance')
lDens.set_ylabel('% Civilians Alive', color='b')
lDens.tick_params('y', colors='b')

lDens2 = lDens.twinx()
lDens2.plot(agentMeans, enemiesKilledMeans, 'r--')
lDens2.set_ylabel('% Enemies Killed', color='r')
lDens2.tick_params('y', colors='r')
lDens.set_title('Total Results')
lDens.axis([0.0, 1.0, 0.0, 1.0])
lDens2.axis([0.0, 1.0, 0.0, 1.0])

# ## MED-DENSITY
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT agentMean, enemiesKilled, civsLiving FROM data WHERE density=0.2'):
    agentMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[agentMean].append(enemiesKilled)
    civsLivingDict[agentMean].append(civsLiving)
agentMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[agentMean]) for agentMean in agentMeans]
civsLivingMeans = [mean(civsLivingDict[agentMean]) for agentMean in agentMeans]
mDens.plot(agentMeans, civsLivingMeans, 'b--')
mDens.set_xlabel('Agent Compliance')
mDens.set_ylabel('% Civilians Alive', color='b')
mDens.tick_params('y', colors='b')

mDens2 = mDens.twinx()
mDens2.plot(agentMeans, enemiesKilledMeans, 'r--')
mDens2.set_ylabel('% Enemies Killed', color='r')
mDens2.tick_params('y', colors='r')
mDens.set_title('Total Results')
mDens.axis([0.0, 1.0, 0.0, 1.0])
mDens2.axis([0.0, 1.0, 0.0, 1.0])

# #HIGH-DENSITY
enemiesKilledDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
civsLivingDict = {0.:[], 0.25:[], 0.5:[], 0.75:[], 1.0:[]}
for row in c.execute('SELECT agentMean, enemiesKilled, civsLiving FROM data WHERE density=0.4'):
    agentMean, enemiesKilled, civsLiving = row
    enemiesKilledDict[agentMean].append(enemiesKilled)
    civsLivingDict[agentMean].append(civsLiving)
agentMeans = [0.0, 0.25, 0.5, 0.75, 1.0]
enemiesKilledMeans = [mean(enemiesKilledDict[agentMean]) for agentMean in agentMeans]
civsLivingMeans = [mean(civsLivingDict[agentMean]) for agentMean in agentMeans]
hDens.plot(agentMeans, civsLivingMeans, 'b--')
hDens.set_xlabel('Agent Compliance')
hDens.set_ylabel('% Civilians Alive', color='b')
hDens.tick_params('y', colors='b')

hDens2 = hDens.twinx()
hDens2.plot(agentMeans, enemiesKilledMeans, 'r--')
hDens2.set_ylabel('% Enemies Killed', color='r')
hDens2.tick_params('y', colors='r')
hDens.set_title('Total Results')
hDens.axis([0.0, 1.0, 0.0, 1.0])
hDens2.axis([0.0, 1.0, 0.0, 1.0])

killsLivesvsAgt.tight_layout()

# ENEMY DEATHS AND CIVILIANS LIVING COMPARISON
deasthsVsLives, deathsLives = plt.subplots(1, num='Enemy Deaths and Civilian Survival')
## TOTAL
enemiesKilled = []
civsLiving = []
for row in c.execute('SELECT enemiesKilled, civsLiving FROM data'):
    enemiesKilled.append(row[0])
    civsLiving.append(row[1])
deathsLives.plot(enemiesKilled, civsLiving, 'bo')
deathsLives.set_xlabel('% Enemies Killed')
deathsLives.set_ylabel('% Civilians Alive')
deathsLives.axis([0.0, 1.0, 0.0, 1.0])
plt.show()
