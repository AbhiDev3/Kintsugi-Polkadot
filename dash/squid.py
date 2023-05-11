# -*- coding: utf-8 -*-
"""Kintsugi Analysis

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RfRWb2flzmzBn7S9OFeJw2yo3SLKMpcA

Let's analyze Kintsugi's vaults and early investors. For that, we will use several subsquids.

Kintsugi-X is a subsquid built by the Kintsugi-X team for the purpose of analysing transfers.
"""

import requests
import json
import pandas as pd

kintsugi = "https://api-kusama.interlay.io/graphql/graphql"
kintsugi_2 = "wss://api-kusama.interlay.io/parachain"
kusama = "https://app.gc.subsquid.io/beta/kusama-explorer/v1/graphql"
kintsugi_x = "https://app.gc.subsquid.io/beta/kintsugi-x/v3/graphql"

"""One of the interesting questions is: do vaults self-mint?"""

def is_equal(row):
    return row["userParachainAddress"] == row['vault.accountId']

"""Let's start creating a directory of interesting Kintsugi addresses.
This info comes from the Interlay discord server, "meet the vaults".
"""

kts = {
    "a3eZhSC12zE4D49ir4QkxZwDC3jU6iwNQ953ZZzQsCLTnPJjs": ['Simon Kraus'],
    "a3bccyaV6tCoqaWqByeqvXo5kBbd1m4yCPKyX937HB1APTt7Y": ['rodrigo.barrios', 'hypersphere'],
    "a3bzFrZ5kXYpaaD5NbapUDSfjZPQTWFKGwSbMmGeRAL8BGrCs": ['@boyswan'],
    "a3btcmyVE6ENtWVyHiX9QnorJfKfA2TsSCF43urDeNAWKueH6": ['@seergeist'],
    "a3dh62XsvNmtPAzfwCH9bv34dqPFzjKcWBi5mYM93mKmMt64s": ['@DkA7s'],
    "a3dh7jXhw2q7vqUpEPAb8BeFTNqXXvG9zBf7hsfm3o9hNbjtK": ['@whisperit'],
    "a3aDPraojQvYhVHjyVuYRFXno58EPMjegrY9nubPmpck2X7JS": ['@blinkin', 'chaos DAO'],
    "a3azGTG3qGmUuQckCKjFAhfjfnnRAXmpgV4fPVPziNaA1zCwG": ['@marvel'],
    "a3eKvTxY56smUwHU9vLpw9w5kSqpoPkJskU2tNxUSHAnntQTS": ['@mafux777'],
    "a3cCyigH5pLJXcLKRNGFaBnx3a7diTXq9pPZ1TB8XWgqeCQvW": ['@spazcoin', 'chaos DAO', 'VaaS'],
    "a3baaLbC1JMHJLJ2HwEQMz3S5VuiCWBYy4i66Ziq1vXzmVU6b": ['@spazcoin', 'chaos DAO'],
    "a3fudELrRCjuSyYEPkRAKFQyjzo5YyU228LdqinGsnjBUNB8P": ['@spazcoin', 'chaos DAO', 'VaaS'],
    "a3cCyigH5pLJXcLKRNGFaBnx3a7diTXq9pPZ1TB8XWgqeCQvW": ['@spazcoin', 'chaos DAO'],
    "a3fcMNTjXcJSwAVnTNKwwP7T8XM2bCW7FshsTW2hpUTrdXzed": ['@spazcoin', 'chaos DAO'],
    "a3aPvmjypKaDtjRgYbDL2CCkseYR3SLwvPevL6j7wF67aFtV4": ['@timbotronic'],
    "a3fZSzXxTZYY58BQrfhJx8cDtp4wRdbZ8X4ReF2iUT63y5RcX": ['@0xvault'],
    "a3dJfVzssBJgBmRuMZBre5H71rvawHJoFvFHGz2Aq7Hdt492w": ['@niko'],
    "a3eFe9M2HbAgrQrShEDH2CEvXACtzLhSf4JGkwuT9SQ1EV4ti": ['@paride'],
    "a3cAyFZMgahPoAyWbNRrjX2TnXQtpS3bztCVMNuLNcTYATBte": ['@dan', 'interlay'],
    "a3azPeBMe1EexQvFMd5otaV4q4fPN3Ya5aBQhaChpGzbhLPpe": ['pumpernickel'],
    "a3dMJSmFcqTDpvRPfM2HKn7CHd5uw3G7atogtxXeXru3LGURE": ['@alibaba'],
    "a3cDUVdQi8FqkiUBMjqS3RBWPghRWFXBwjRzKZvmB3MmHLDcP": ['@alibaba'],
    "a3aGT3FRF1WgWtWdi8VmhB3YEJVE6XtrvT41TqcKFxZbuUvS1": ['@warinelly'], # info provided by @quin
}

"""Let's create a method to add labels to our list."""

def add_label_to_list(my_list, label):
  for a in my_list:
    if a not in kts:
      kts[a] = []
    if label not in kts[a]:
      kts[a].append(label)

def enrich_df(df, col):
  df[f'label_{col}'] = df[col].apply(lambda v: "/".join(kts.get(v, [])))

"""Let's create a query to understand transfers from Kusama (Relay Chain) to Kintsugi. These have to be KSM transfers, because Kusama itself does not handle other assets.
We assume that all of these will end up as collateral. 

"""



def fetch_kusama_transfers():
  q = """
    query MyQuery {
      transfers(where: {name_eq: "xcmPallet.reserveTransferAssets", AND: {to: {id_eq: "F7fq1inhrJsYSUkWhyZ3zqtp5K3AKBBjbPWy6VLiRGHipPi"}}}, orderBy: date_DESC) {
        name
        amount
        from {
          id
        }
        date
        to {
          id
        }
      }
    }
  """

  r = requests.post("https://app.gc.subsquid.io/beta/kusama-explorer/v1/graphql", json={"query" : q}).json()
  df_0 = pd.json_normalize(r['data']['transfers'])
  df_0['ksm'] = df_0['amount'].apply(lambda x: float(x) / 1e12)
  kusama_transfers = df_0.groupby('from.id').agg(dict(ksm="sum", date="min")).sort_values('ksm', ascending=False)
  kusama_transfers.reset_index(inplace=True)
  return kusama_transfers

"""Now that we know the biggest KSM senders, we should calculate their Kintsugi address. (TO DO IN PYTHON)
(We use a workaround later)
"""

def fetch_vaults():
  q_redeems = """query MyQuery {
    redeems(orderBy: request_timestamp_ASC) {
      id
      request {
        requestedAmountBacking
        timestamp
        height {
          absolute
          active
        }
      }
      userParachainAddress
      vault {
        accountId
        collateralToken
        wrappedToken
      }
      userBackingAddress
      bridgeFee
      btcTransferFee
      collateralPremium
      status
      execution {
        height {
          absolute
          active
        }
        timestamp
      }
      cancellation {
        timestamp
        slashedCollateral
        reimbursed
        height {
          absolute
          active
        }
      }
    }
  }
  """

  """Let's use the official Kintsugi squid to download data about issue requests."""

  q_issues = """query MyQuery {
    issues(orderBy: request_timestamp_DESC, limit: 10000, offset: 0) {
      id
      request {
        amountWrapped
        bridgeFeeWrapped
        timestamp
        height {
          absolute
          active
        }
      }
      userParachainAddress
      vault {
        accountId
        collateralToken
        wrappedToken
      }
      vaultBackingAddress
      vaultWalletPubkey
      griefingCollateral
      status
      refund {
        amountPaid
        btcAddress
        btcFee
        executionHeight {
          absolute
          active
        }
        executionTimestamp
        id
        requestHeight {
          absolute
          active
        }
        requestTimestamp
      }
      execution {
        height {
          absolute
          active
        }
        amountWrapped
        bridgeFeeWrapped
        timestamp
      }
      cancellation {
        timestamp
        height {
          absolute
          active
        }
      }
    },
  }
  """

  # Obtain a list of all redemptions and summarize them a bit
  r = requests.post(kintsugi, json={"query" : q_redeems}).json()
  df_1 = pd.json_normalize(r['data']['redeems'])
  df_1['btc'] = df_1['request.requestedAmountBacking'].apply(lambda x: float(x) / -1e8)
  df_1['self'] = df_1.apply(is_equal, axis=1)
  df_1['action'] = "redeem"

  # Obtain a list of all issue executions and summarize them a bit
  # issue_query = get_query_text_from_file("issue")
  r = requests.post(kintsugi, json={"query" : q_issues}).json()
  df_2 = pd.json_normalize(r['data']['issues'])
  df_2['btc'] = df_2['request.amountWrapped'].apply(lambda x: float(x) / 1e8)
  df_2['self'] = df_2.apply(is_equal, axis=1)
  df_2['action'] = "issue"

  cols_1 = set(df_1.columns) - set(df_2.columns)
  cols_2 = set(df_2.columns) - set(df_1.columns)


  """Let's download data about redemptions, so we can net out issues and redemptions for calculating the vault sizes.
  TODO: This analysis should also include Theft and Replacement.
  Since redemptions are negative, the 20% quantile includes the biggest redemptions
  """

  redeems = df_1.groupby('userParachainAddress').agg({'btc':sum}).sort_values('btc', ascending=True)
  redeems['btc'] = redeems.btc.apply(lambda x: -x)
  q = redeems.btc.quantile(.8)
  top_redeemers = redeems[redeems.btc>q].index
  add_label_to_list(top_redeemers, 'Top Redeemer')
  redeems['btc'] = redeems.btc.apply(lambda x: -x)

  issues = df_2.groupby('userParachainAddress').agg({'btc':sum}).sort_values('btc', ascending=False)
  q = issues.btc.quantile(.8)
  top_issues = issues[issues.btc>q].index
  add_label_to_list(top_issues, 'Top Issuer')

  self_issuers = df_2[df_2.self==True]
  self_issuers.groupby("userParachainAddress").agg(dict(btc=sum)).sort_values("btc", ascending=False)

  """Let's consolidate this info and merge the two dataframes so we can net out the issue requests and the redeem requests."""

  merged_df = pd.concat([
      df_1.loc[df_1.status=='Completed', ['vault.accountId', 'btc', 'request.timestamp', 'self']],
      df_2.loc[df_2.status=='Completed', ['vault.accountId', 'btc', 'request.timestamp', 'self']],
                        ]).sort_values('request.timestamp')
  # apportion BTC to self or other
  merged_df['btc_self'] = merged_df.apply(lambda b: b.btc if b.self else 0, axis=1)
  merged_df['btc_other'] = merged_df.apply(lambda b: b.btc if not b.self else 0, axis=1)
  # add up the BTC depending on self/other
  biggest_vaults = merged_df.groupby('vault.accountId').agg(dict(btc_self='sum', btc_other='sum', btc='sum')).sort_values('btc', ascending=False)
  biggest_vaults['social'] = biggest_vaults.apply(lambda b: True if b.btc_self<0.2*b.btc else False, axis=1)
  biggest_vaults['selfish'] = biggest_vaults.apply(lambda b: True if b.btc_self>0.8*b.btc else False, axis=1)
  add_label_to_list(biggest_vaults.loc[biggest_vaults.social].index, 'Social')
  add_label_to_list(biggest_vaults.loc[biggest_vaults.selfish].index, 'Selfish')


  biggest_vaults.reset_index(inplace=True)
  enrich_df(biggest_vaults, "vault.accountId")
  total_btc = biggest_vaults.btc.sum()
  biggest_vaults['share'] = biggest_vaults.btc.apply(lambda btc: f"{btc/total_btc:.1%}")

  vaults = biggest_vaults.reset_index()
  del vaults['index']
  vaults = vaults.rename(columns={"vault.accountId":"vault"})
  add_label_to_list(list(vaults.vault.iloc[0:20]), "Top 20 Vault")
  add_label_to_list(list(vaults.vault.loc[vaults.vault.isin(self_issuers.userParachainAddress)].iloc[0:20]), "Self Issuer")
  enrich_df(vaults, 'vault')
  vaults.iloc[0:25]

  return vaults




def fetch_transfers(vaults, kusama_transfers):
  q_kintsugix="""
  query MyQuery {
    transfers(orderBy: timestamp_DESC) {
      amount
      from {
        karura
        kintsugi
        kusama
        moonriver
        id
      }
      fromChain
      timestamp
      to {
        id
        karura
        kintsugi
        kusama
        moonriver
      }
      toChain
      token
    }
  }

  """

  r = requests.post(kintsugi_x, json={"query" : q_kintsugix}).json()
  xtoken_transfers = pd.json_normalize(r['data']['transfers'])

  master_t = dict(
      KSM = 1e12,
      BTC = 1e8,
      KBTC = 1e8,
      KINT = 1e12,
  )

  def fix_currency(row):
      token = row['token']
      divisor = master_t.get(token, 1.0)
      row[token.lower()] = float(row.get('amount', 0.0)) / divisor
      return row

  """Where did the biggest vaults send their tokens to or receive tokens from?

  Let's see who the vault owners got the KINT from to start
  """

  xtoken_transfers.rename(columns={"from.id":"from_id", "to.id":"to_id"}, inplace=True)
  xtoken_transfers = xtoken_transfers.apply(fix_currency, axis=1)

  xtoken_transfers.timestamp.max()

  """There are a few accounts involved in crowdloans and other "shenanigans". Let's label them, too. """

  shenanigans = xtoken_transfers.loc[xtoken_transfers.toChain==2092].groupby('from_id').agg(dict(kint=sum, to_id='nunique'))
  shenanigans.sort_values('to_id', ascending=False).iloc[0:20]

  """That analysis seems to suggest we should label the ones which sent more than 6 KINT as "shenanigans"...

  """

  shenanigans_list = shenanigans.loc[shenanigans.to_id>6].index
  shenanigans.reset_index(inplace=True)
  enrich_df(shenanigans, 'from_id')

  add_label_to_list(shenanigans_list, "shenanigans")
  enrich_df(shenanigans, 'from_id')
  shenanigans.sort_values('to_id', ascending=False).iloc[0:20]

  """Who are the accounts that have sent KINT or KSM to the top 20 vaults? We shall exclude "shenanigans".

  to_id: the top 20 vaults

  from_id: the accounts sending KINT excluding shenanigans
  """

  funding_accounts = xtoken_transfers.loc[
                                          (xtoken_transfers.to_id.isin(vaults.iloc[0:20, 0])) & 
                                          ~(xtoken_transfers.from_id.isin(shenanigans_list)) & 
                                          (xtoken_transfers.toChain==2092)
                                          ].groupby(['to_id', 'from_id', 'from.kusama','fromChain']).agg(dict(kint=sum, ksm=sum, timestamp=min))
  funding_accounts.reset_index(inplace=True)
  funding_accounts.rename(columns=dict(to_id="vault", from_id="daddy"), inplace=True)
  funding_accounts.sort_values('timestamp')

  """Let's label each daddy with his vault"""

  for n, row in funding_accounts.iterrows():
    vault = row['vault'][-5:]
    daddy = row['daddy']
    add_label_to_list([daddy], f'Daddy of {vault}')  
    add_label_to_list([row['vault']], f'{vault}')

  add_label_to_list(funding_accounts.daddy, "Likely Vault Owner")
  enrich_df(funding_accounts, 'vault')
  enrich_df(funding_accounts, 'daddy')
  funding_accounts = funding_accounts.sort_values('ksm', ascending=False).loc[:, ['label_vault', 'label_daddy', 'kint', 'ksm']]


  """Of the funders, which ones do we know from the KSM analysis?"""

  # Hard way to create a lookup table from KSM to KINT
  a=xtoken_transfers.groupby(['from.kusama','from_id']).size()
  b = a.reset_index()
  b.index = b['from.kusama']
  del b['from.kusama']

  ksm_to_kint = dict(b['from_id'])

  kusama_transfers['kintsugi'] = kusama_transfers['from.id'].apply(lambda k: ksm_to_kint.get(k, ''))
  k = kusama_transfers.loc[kusama_transfers.ksm>50]
  add_label_to_list(k.kintsugi, 'K>50')
  enrich_df(k, 'kintsugi')

  """What do people do with their KBTC?"""

  my_currencies = ['kint', 'ksm', 'kbtc']

  # def add_more_labels(my_currency):
  agg = {}
  for c in my_currencies:
    agg[c] = sum

  agg['timestamp'] = "min"

  top_transfer = xtoken_transfers.groupby(['from_id', 'fromChain','to_id', 'toChain']).agg(agg)
  top_transfer.reset_index(inplace=True)


  for my_currency in my_currencies:
    q = top_transfer[my_currency].quantile(.8)

    top_transfer_ids = top_transfer[top_transfer[my_currency]>q].from_id
    add_label_to_list(top_transfer_ids, f'Top {my_currency.upper()} Mover')

    top_transfer_ids = top_transfer[top_transfer[my_currency]>q].to_id
    add_label_to_list(top_transfer_ids, f'Top {my_currency.upper()} Sink')

  enrich_df(top_transfer, 'from_id')
  enrich_df(top_transfer, 'to_id')

  top_transfer.sort_values('kbtc', ascending=False)

  """Same story, but with KINT - removing two accounts which seem to be system accounts"""

  agg['to_id']='nunique'
  agg['timestamp']='min'
  xtoken_transfers['last_seen'] = xtoken_transfers.timestamp # workaround to agg this col, too
  agg['last_seen']='max'

  top_transfer_from = xtoken_transfers.groupby(['from_id', 'fromChain','toChain']).agg(agg)
  top_transfer_from.kint = top_transfer_from.kint.apply(lambda k: round(k))
  top_transfer_from = top_transfer_from.reset_index(inplace=False)

  exclude = top_transfer_from.sort_values('kint', ascending=False).iloc[0:2, 0]
  add_label_to_list(exclude, 'KINT System?')
  enrich_df(top_transfer_from, 'from_id')

  top_transfer_from.sort_values('kint', ascending=False)

  def calc_secs(row):
    return (pd.Timestamp(row['last_seen'])-pd.Timestamp(row['timestamp'])) // pd.Timedelta("1s")

  enrich_df(top_transfer_from, 'from_id')
  top_transfer_from['duration'] = top_transfer_from.apply(calc_secs, axis=1)

  enrich_df(xtoken_transfers, 'from_id')
  enrich_df(xtoken_transfers, 'to_id')

  return top_transfer, xtoken_transfers, funding_accounts

