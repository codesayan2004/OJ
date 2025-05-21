#include<bits/stdc++.h>
#define int long long
#define pb push_back
#define ff first
#define ss second
#define mpr make_pair
#define all(x) (x).begin(), (x).end()
#define vi vector<int>
#define vpi vector<pair<int,int> >
#define pi pair<int,int>
#define endl "\n"
#define sayan_code ios::sync_with_stdio(false);cin.tie(0)
using namespace std;
#define print(x) { \
    for (auto it: x) { \
        cout << it << " "; \
    } \
    cout << "\n"; \
}
#define print_pair(x) { \
    for (auto it: x) { \
        cout << it.ff << ": "<< it.ss<<", "; \
    } \
    cout<<"\n"; \
}
int mod = 1e9+7;
int f(int n, vi& dp){
    if (n==0) return 1;
    if (n<0) return 0;
    if (dp[n] != -1) return dp[n];
    int cnt = 0;
    for(int k=1; k<=6; k++){
        cnt = (cnt + f(n-k, dp))%mod;
    }
    return dp[n] = cnt%mod;
}
void Solve(){
    int n;
    cin>>n;
    vi dp(n+1,-1);
    cout<<f(n,dp)<<"\n";
}
signed main(){
    Solve();
}

/*
Author: Sayan Mandal
Codeforces handle: @sayan_mandal
*/

