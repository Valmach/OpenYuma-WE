import logging
import subprocess

import wireless_emulator.emulator

logger = logging.getLogger(__name__)

class Link:
    linkNumber = 1
    def __init__(self, linkEnds):
        self.linkEnds =  linkEnds
        self.emEnv = wireless_emulator.emulator.Emulator()
        self.bridgeName = None
        self.linkId = None

        self.interfacesObj = []

        if len(linkEnds) != 2:
            logger.critical("Incorrect link defined in JSON config file. It does not contain exactly two interfaces!")
            raise ValueError("Incorrect link defined in JSON config file. It does not contain exactly two interfaces!")

        if self.validateLinkEnds() is False:
            logger.critical("Interfaces defining link not valid: ", linkEnds[0], linkEnds[1])
            raise ValueError("Interfaces defining link not valid: ", linkEnds[0], linkEnds[1])

        logger.debug("Link object was created")

    def validateLinkEnds(self):

        for ne in self.emEnv.networkElementList:
            neUuid = ne.getNeUuid()
            logger.debug("Validating for NE=%s", neUuid)
            if neUuid == self.linkEnds[0]['uuid']:
                logger.debug("Gettinf interface for NE=%s", neUuid)
                intfObj = ne.getInterfaceFromInterfaceUuid(self.linkEnds[0]['ltp'])
                if intfObj is not None:
                    self.interfacesObj.append(intfObj)
                else:
                    logger.debug("Interface=%s not found in NE=%s", self.linkEnds[0]['ltp'], neUuid)
            elif neUuid == self.linkEnds[1]['uuid']:
                logger.debug("Gettinf interface for NE=%s", neUuid)
                intfObj = ne.getInterfaceFromInterfaceUuid(self.linkEnds[1]['ltp'])
                if intfObj is not None:
                    self.interfacesObj.append(intfObj)
                else:
                    logger.debug("Interface=%s not found in NE=%s", self.linkEnds[0]['ltp'], neUuid)

        if len(self.interfacesObj) != 2:
            return False

        return True

    def addLink(self):
        print("Adding link between NE %s interface %s and NE %s interface %s..." %
              (self.interfacesObj[0].getNeName(), self.interfacesObj[0].getInterfaceUuid(),
               self.interfacesObj[1].getNeName(), self.interfacesObj[0].getInterfaceUuid()))
        logger.debug("Adding link between interfaces %s and %s",
                     self.interfacesObj[0].getInterfaceUuid(), self.interfacesObj[1].getInterfaceUuid())

        ipInterfaceNetwork = self.emEnv.intfIpFactory.getFreeInterfaceIp()

        firstIpOfLink = str(ipInterfaceNetwork[1])
        secondIpOfLink = str(ipInterfaceNetwork[2])

        self.interfacesObj[0].setIpAddress(firstIpOfLink)
        self.interfacesObj[1].setIpAddress(secondIpOfLink)

        self.bridgeName = "oywe-br-" + str(Link.linkNumber)

        stringCmd = "ovs-vsctl add-br %s" % (self.bridgeName)
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Could not add bridge for link. Stderr: %s", strLine)
            raise RuntimeError
        logger.debug("Added bridge %s for link.", self.bridgeName)

        self.linkId = Link.linkNumber
        Link.linkNumber += 1

        stringCmd = "ovs-docker add-port %s %s %s --ipaddress=%s/30 --macaddress=%s" % \
                    (self.bridgeName, self.interfacesObj[0].getInterfaceName(), self.interfacesObj[0].getNeName(),
                     firstIpOfLink, self.interfacesObj[0].getMacAddress())
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Could not add interface. Stderr: %s", strLine)
            raise RuntimeError
        logger.debug("Added port for interface %s from NE=%s having IP=%s ",
                     self.interfacesObj[0].getInterfaceName(), self.interfacesObj[0].getNeName(),
                     firstIpOfLink)

        stringCmd = "ovs-docker add-port %s %s %s --ipaddress=%s/30 --macaddress=%s" % \
                    (self.bridgeName, self.interfacesObj[1].getInterfaceName(), self.interfacesObj[1].getNeName(),
                     secondIpOfLink, self.interfacesObj[1].getMacAddress())
        cmd = subprocess.Popen(stringCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in cmd.stderr:
            strLine = line.decode("utf-8").rstrip('\n')
            logger.critical("Could not add interface. Stderr: %s", strLine)
            raise RuntimeError
        logger.debug("Added port for interface %s from NE=%s having IP=%s ",
                     self.interfacesObj[1].getInterfaceName(), self.interfacesObj[1].getNeName(),
                     secondIpOfLink)