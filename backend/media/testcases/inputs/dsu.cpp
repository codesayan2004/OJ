#include<iostream>
#include<vector>
using namespace std;

class dsu{
    vector<int> parent, rank, size;
public:
    dsu(int n){
        parent.resize(n+1);
        rank.resize(n+1);
        size.resize(n+1);
        for(int i=0; i<=n; i++){
            parent[i]=i;
            rank[i]=0;
            size[i]=1;
        }
    }
    int getParent(int node){
        if (parent[node] == node) return node;
        return parent[node] = getParent(parent[node]);
    }
    void unionByRank(int u, int v){
        int paru = getParent(u);
        int parv = getParent(v);
        if (paru == parv) return;
        if (rank[paru] > rank[parv]) parent[parv] = paru;
        else if (rank[paru] < rank[parv]) parent[paru] = parv;
        else{
            rank[paru]++;
            parent[parv] = paru;
        }
    }
    void unionBySize(int u, int v){
        int paru = getParent(u);
        int parv = getParent(v);
        if (paru == parv) return;
        if (size[paru] > size[parv]){
            parent[parv] = paru;
            size[paru] += size[parv]; 
        }
        else {
            parent[paru] = parv;
            size[parv] += size[paru];
        }
    }
};
int main(){
    dsu set(10);
    set.unionBySize(5,6);
    set.unionBySize(1,2);
    set.unionBySize(5,2);
    set.unionBySize(10,9);
    set.unionBySize(8,7);
    set.unionBySize(10,8);
    //set.unionBySize(9,2);
    cout<<set.getParent(1)<<"\n";
    cout<<set.getParent(5)<<"\n";
    cout<<set.getParent(2)<<"\n";
    cout<<set.getParent(9)<<"\n";
    cout<<set.getParent(7)<<"\n";
}