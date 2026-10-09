import { PageHeader } from "../components/ui.jsx";
import TransactionSearch from "../components/TransactionSearch.jsx";
import { useRole } from "../utils/roleGuard.jsx";

export default function Transactions() {
  const { can } = useRole();

  return (
    <>
      <PageHeader
        title="Transactions"
        subtitle="Search by date, amount, status or card, with sorting and pagination."
      />
      <TransactionSearch endpoint="/transactions/search" />

      {can("txn:view") && (
        <div className="mt-10">
          <h2 className="mb-3 text-lg font-semibold">All customers (staff view)</h2>
          <TransactionSearch endpoint="/admin/transactions/search" showUser />
        </div>
      )}
    </>
  );
}