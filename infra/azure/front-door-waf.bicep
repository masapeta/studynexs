// Azure Front Door Standard/Premium + WAF — StudyNexs API edge
// SECURITY-REVIEW: WAF mode should start as Detection in production rollout.

@description('Azure region for Front Door (global resource, metadata only)')
param location string = 'global'

@description('Front Door profile name')
param profileName string = 'studynexs-fd'

@description('Public hostname for API (CNAME target)')
param apiBackendHost string

@description('Origin hostname (Container Apps FQDN)')
param apiBackendAddress string

@description('WAF mode: Detection or Prevention')
@allowed(['Detection', 'Prevention'])
param wafPolicyMode string = 'Detection'

param wafPolicyName string = 'studynexswaf'

resource waf 'Microsoft.Network/frontDoorWebApplicationFirewallPolicies@2022-05-01' = {
  name: wafPolicyName
  location: location
  sku: {
    name: 'Premium_AzureFrontDoor'
  }
  properties: {
    policySettings: {
      enabledState: 'Enabled'
      mode: wafPolicyMode
      requestBodyCheck: 'Enabled'
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'Microsoft_DefaultRuleSet'
          ruleSetVersion: '2.1'
          ruleGroupOverrides: []
        }
        {
          ruleSetType: 'Microsoft_BotManagerRuleSet'
          ruleSetVersion: '1.0'
          ruleGroupOverrides: []
        }
      ]
    }
    customRules: {
      rules: [
        {
          name: 'RateLimitPerIP'
          enabledState: 'Enabled'
          priority: 100
          ruleType: 'RateLimitRule'
          rateLimitDurationInMinutes: 1
          rateLimitThreshold: 1000
          matchConditions: [
            {
              matchVariable: 'RemoteAddr'
              operator: 'IPMatch'
              negateCondition: false
              matchValue: ['0.0.0.0/0']
              transforms: []
            }
          ]
          action: 'Block'
        }
      ]
    }
  }
}

resource profile 'Microsoft.Cdn/profiles@2023-05-01' = {
  name: profileName
  location: location
  sku: {
    name: 'Premium_AzureFrontDoor'
  }
}

resource endpoint 'Microsoft.Cdn/profiles/afdEndpoints@2023-05-01' = {
  parent: profile
  name: 'studynexs-api'
  location: location
  properties: {
    enabledState: 'Enabled'
  }
}

resource originGroup 'Microsoft.Cdn/profiles/originGroups@2023-05-01' = {
  parent: profile
  name: 'api-origin-group'
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 2
    }
    healthProbeSettings: {
      probePath: '/health'
      probeRequestType: 'GET'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 30
    }
  }
}

resource origin 'Microsoft.Cdn/profiles/originGroups/origins@2023-05-01' = {
  parent: originGroup
  name: 'api-origin'
  properties: {
    hostName: apiBackendAddress
    httpPort: 80
    httpsPort: 443
    originHostHeader: apiBackendHost
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
  }
}

resource route 'Microsoft.Cdn/profiles/afdEndpoints/routes@2023-05-01' = {
  parent: endpoint
  name: 'api-route'
  properties: {
    originGroup: {
      id: originGroup.id
    }
    supportedProtocols: ['Http', 'Https']
    patternsToMatch: ['/*']
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
  }
}

resource securityPolicy 'Microsoft.Cdn/profiles/securityPolicies@2023-05-01' = {
  parent: profile
  name: 'api-waf-policy'
  properties: {
    parameters: {
      type: 'WebApplicationFirewall'
      wafPolicy: {
        id: waf.id
      }
      associations: [
        {
          domains: [
            {
              id: endpoint.properties.hostName
            }
          ]
          patternsToMatch: ['/*']
        }
      ]
    }
  }
}

output frontDoorEndpointHostName string = endpoint.properties.hostName
output wafPolicyId string = waf.id
