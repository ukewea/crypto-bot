import React from 'react';
import { ArrowUpCircle, ArrowDownCircle, Clock } from 'lucide-react';
import type { Transaction } from '../types/trading';
import { formatCurrency, formatDate } from '../utils/dataParser';

interface TransactionHistoryProps {
  transactions: Transaction[];
  symbol: string;
}

const TransactionHistory: React.FC<TransactionHistoryProps> = ({ transactions, symbol }) => {
  const sortedTransactions = [...transactions].sort((a, b) => 
    parseInt(b.time) - parseInt(a.time)
  );

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
        <Clock className="mr-3 text-blue-600" />
        Transaction History - {symbol}
      </h3>

      {sortedTransactions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No transactions found</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-2 font-semibold text-gray-700">Date</th>
                <th className="text-left py-3 px-2 font-semibold text-gray-700">Type</th>
                <th className="text-right py-3 px-2 font-semibold text-gray-700">Quantity</th>
                <th className="text-right py-3 px-2 font-semibold text-gray-700">Price</th>
                <th className="text-right py-3 px-2 font-semibold text-gray-700">Total</th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction, index) => {
                const quantity = parseFloat(transaction.quantity);
                const price = parseFloat(transaction.price);
                const total = quantity * price;
                const isBuy = transaction.activity === 'BUY';

                return (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2 text-sm text-gray-600">
                      {formatDate(transaction.time)}
                    </td>
                    <td className="py-3 px-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        isBuy 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {isBuy ? (
                          <ArrowDownCircle size={12} className="mr-1" />
                        ) : (
                          <ArrowUpCircle size={12} className="mr-1" />
                        )}
                        {transaction.activity}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-right text-sm font-mono">
                      {quantity.toFixed(8)} {symbol}
                    </td>
                    <td className="py-3 px-2 text-right text-sm font-mono">
                      {formatCurrency(price)}
                    </td>
                    <td className={`py-3 px-2 text-right text-sm font-mono font-semibold ${
                      isBuy ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {isBuy ? '-' : '+'}{formatCurrency(total)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TransactionHistory;