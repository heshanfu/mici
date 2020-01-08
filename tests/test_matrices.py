import mici.matrices as matrices
import numpy as np
import numpy.linalg as nla
import scipy.linalg as sla
import numpy.testing as npt
from functools import partial, wraps

AUTOGRAD_AVAILABLE = True
try:
    import autograd.numpy as anp
    from autograd import grad
except ImportError:
    AUTOGRAD_AVAILABLE = False
    import warnings
    warnings.warn(
        'Autograd not available. Skipping gradient tests.')

SEED = 3046987125
NUM_SCALAR = 4
NUM_VECTOR = 4
SIZES = {1, 2, 5, 10}
ATOL = 1e-10


def iterate_over_matrix_pairs(test):

    @wraps(test)
    def iterated_test(self):
        for matrix_pair in self.matrix_pairs.values():
            yield (test, *matrix_pair)

    return iterated_test


def iterate_over_matrix_pairs_vectors(test):

    @wraps(test)
    def iterated_test(self):
        for key, (matrix, np_matrix) in self.matrix_pairs.items():
            for vector in self.vectors[np_matrix.shape[0]]:
                yield test, matrix, np_matrix, vector

    return iterated_test


def iterate_over_matrix_pairs_premultipliers(test):

    @wraps(test)
    def iterated_test(self):
        for key, (matrix, np_matrix) in self.matrix_pairs.items():
            for pre in self.premultipliers[np_matrix.shape[0]]:
                yield test, matrix, np_matrix, pre

    return iterated_test


def iterate_over_matrix_pairs_postmultipliers(test):

    @wraps(test)
    def iterated_test(self):
        for key, (matrix, np_matrix) in self.matrix_pairs.items():
            for post in self.postmultipliers[np_matrix.shape[1]]:
                yield test, matrix, np_matrix, post

    return iterated_test


def iterate_over_matrix_pairs_scalars(test):

    @wraps(test)
    def iterated_test(self):
        for matrix, np_matrix in self.matrix_pairs.values():
            for scalar in self.scalars:
                yield test, matrix, np_matrix, scalar

    return iterated_test


def iterate_over_matrix_pairs_scalars_postmultipliers(test):

    @wraps(test)
    def iterated_test(self):
        for matrix, np_matrix in self.matrix_pairs.values():
            for scalar in self.scalars:
                for post in self.postmultipliers[np_matrix.shape[1]]:
                    yield test, matrix, np_matrix, scalar, post

    return iterated_test


def iterate_over_matrix_pairs_scalars_premultipliers(test):

    @wraps(test)
    def iterated_test(self):
        for matrix, np_matrix in self.matrix_pairs.values():
            for scalar in self.scalars:
                for pre in self.premultipliers[np_matrix.shape[0]]:
                    yield test, matrix, np_matrix, scalar, pre

    return iterated_test


class MatrixTestCase(object):

    def __init__(self, matrix_pairs, rng=None):
        self.matrix_pairs = matrix_pairs
        self.rng = np.random.RandomState(SEED) if rng is None else rng
        # Ensure a mix of positive and negative scalar multipliers
        self.scalars = np.abs(self.rng.standard_normal(NUM_SCALAR))
        self.scalars[NUM_SCALAR // 2:] = -self.scalars[NUM_SCALAR // 2:]
        self.premultipliers = {
            shape_0: self._generate_premultipliers(shape_0)
            for shape_0 in set(m.shape[0] for _, m in matrix_pairs.values())}
        self.postmultipliers = {
            shape_1: self._generate_postmultipliers(shape_1)
            for shape_1 in set(m.shape[1] for _, m in matrix_pairs.values())}

    def _generate_premultipliers(self, size):
        return (
            [self.rng.standard_normal((size,))] +
            [self.rng.standard_normal((s, size)) for s in [1, size, 2 * size]]
        )

    def _generate_postmultipliers(self, size):
        return (
            [self.rng.standard_normal((size,))] +
            [self.rng.standard_normal((size, s)) for s in [1, size, 2 * size]]
        )

    @iterate_over_matrix_pairs
    def test_shape(matrix, np_matrix):
        assert (
            matrix.shape == (None, None) or matrix.shape == np_matrix.shape)

    @iterate_over_matrix_pairs_postmultipliers
    def test_lmult(matrix, np_matrix, post):
        npt.assert_allclose(matrix @ post, np_matrix @ post)

    @iterate_over_matrix_pairs_premultipliers
    def test_rmult(matrix, np_matrix, pre):
        npt.assert_allclose(pre @ matrix, pre @ np_matrix)

    @iterate_over_matrix_pairs_postmultipliers
    def test_neg_lmult(matrix, np_matrix, post):
        npt.assert_allclose((-matrix) @ post, -np_matrix @ post)

    @iterate_over_matrix_pairs_postmultipliers
    def test_lmult_rmult_trans(matrix, np_matrix, post):
        npt.assert_allclose(matrix @ post, (post.T @ matrix.T).T)

    @iterate_over_matrix_pairs_premultipliers
    def test_rmult_lmult_trans(matrix, np_matrix, pre):
        npt.assert_allclose(pre @ matrix, (matrix.T @ pre.T).T)

    @iterate_over_matrix_pairs_scalars_postmultipliers
    def test_lmult_scalar_lmult(matrix, np_matrix, scalar, post):
        npt.assert_allclose(
            (scalar * matrix) @ post, scalar * np_matrix @ post)

    @iterate_over_matrix_pairs_scalars_postmultipliers
    def test_rdiv_scalar_lmult(matrix, np_matrix, scalar, post):
        npt.assert_allclose(
            (matrix / scalar) @ post, (np_matrix / scalar) @ post)

    @iterate_over_matrix_pairs_scalars_postmultipliers
    def test_rmult_scalar_lmult(matrix, np_matrix, scalar, post):
        npt.assert_allclose(
            (matrix * scalar) @ post, (np_matrix * scalar) @ post)

    @iterate_over_matrix_pairs_scalars_premultipliers
    def test_lmult_scalar_rmult(matrix, np_matrix, scalar, pre):
        npt.assert_allclose(
            pre @ (scalar * matrix), pre @ (scalar * np_matrix))

    @iterate_over_matrix_pairs_scalars_premultipliers
    def test_rmult_scalar_rmult(matrix, np_matrix, scalar, pre):
        npt.assert_allclose(
            pre @ (matrix * scalar), pre @ (np_matrix * scalar))


class ExplicitShapeMatrixTestCase(MatrixTestCase):

    @iterate_over_matrix_pairs
    def test_array(matrix, np_matrix):
        npt.assert_allclose(matrix.array, np_matrix)

    @iterate_over_matrix_pairs
    def test_array_transpose(matrix, np_matrix):
        npt.assert_allclose(matrix.T.array, np_matrix.T)

    @iterate_over_matrix_pairs
    def test_array_transpose_transpose(matrix, np_matrix):
        npt.assert_allclose(matrix.T.T.array, np_matrix)

    @iterate_over_matrix_pairs
    def test_array_numpy(matrix, np_matrix):
        npt.assert_allclose(matrix, np_matrix)

    @iterate_over_matrix_pairs
    def test_diagonal(matrix, np_matrix):
        npt.assert_allclose(matrix.diagonal, np_matrix.diagonal())

    @iterate_over_matrix_pairs_scalars
    def test_lmult_scalar_array(matrix, np_matrix, scalar):
        npt.assert_allclose((scalar * matrix).array, scalar * np_matrix)

    @iterate_over_matrix_pairs_scalars
    def test_rmult_scalar_array(matrix, np_matrix, scalar):
        npt.assert_allclose((matrix * scalar).array, np_matrix * scalar)

    @iterate_over_matrix_pairs_scalars
    def test_rdiv_scalar_array(matrix, np_matrix, scalar):
        npt.assert_allclose((matrix / scalar).array, np_matrix / scalar)

    @iterate_over_matrix_pairs
    def test_neg_array(matrix, np_matrix):
        npt.assert_allclose((-matrix).array, -np_matrix)


class SquareMatrixTestCase(MatrixTestCase):

    def __init__(self, matrix_pairs, rng=None):
        super().__init__(matrix_pairs, rng)
        self.vectors = {
            size: self.rng.standard_normal((NUM_VECTOR, size))
            for size in set(m.shape[0] for _, m in matrix_pairs.values())}

    @iterate_over_matrix_pairs_vectors
    def test_quadratic_form(matrix, np_matrix, vector):
        npt.assert_allclose(
            vector @ matrix @ vector, vector @ np_matrix @ vector)


class ExplicitShapeSquareMatrixTestCase(SquareMatrixTestCase):

    @iterate_over_matrix_pairs
    def test_log_abs_det(matrix, np_matrix):
        npt.assert_allclose(
            matrix.log_abs_det, nla.slogdet(np_matrix)[1], atol=ATOL)


class SymmetricMatrixTestCase(SquareMatrixTestCase):

    @iterate_over_matrix_pairs
    def test_symmetry_identity(matrix, np_matrix):
        assert matrix is matrix.T

    @iterate_over_matrix_pairs_postmultipliers
    def test_symmetry_lmult(matrix, np_matrix, post):
        npt.assert_allclose(matrix @ post, (post.T @ matrix).T)

    @iterate_over_matrix_pairs_premultipliers
    def test_symmetry_rmult(matrix, np_matrix, pre):
        npt.assert_allclose(pre @ matrix, (matrix @ pre.T).T)


class ExplicitShapeSymmetricMatrixTestCase(
        SymmetricMatrixTestCase, ExplicitShapeSquareMatrixTestCase):

    @iterate_over_matrix_pairs
    def test_symmetry_array(matrix, np_matrix):
        npt.assert_allclose(matrix.array, matrix.T.array)

    @iterate_over_matrix_pairs
    def test_eigval(matrix, np_matrix):
        # Ensure eigenvalues in ascending order
        npt.assert_allclose(
            np.sort(matrix.eigval), nla.eigh(np_matrix)[0])

    @iterate_over_matrix_pairs
    def test_eigvec(matrix, np_matrix):
        # Ensure eigenvectors correspond to ascending eigenvalue ordering
        eigval_order = np.argsort(matrix.eigval)
        eigvec = matrix.eigvec.array[:, eigval_order]
        np_eigvec = nla.eigh(np_matrix)[1]
        # Account for eigenvector sign ambiguity when checking for equivalence
        assert np.all(
            np.isclose(eigvec, np_eigvec) | np.isclose(eigvec, -np_eigvec))


class InvertibleMatrixTestCase(MatrixTestCase):

    @iterate_over_matrix_pairs_postmultipliers
    def test_lmult_inv(matrix, np_matrix, post):
        npt.assert_allclose(matrix.inv @ post, nla.solve(np_matrix, post))

    @iterate_over_matrix_pairs_premultipliers
    def test_rmult_inv(matrix, np_matrix, pre):
        npt.assert_allclose(pre @ matrix.inv, nla.solve(np_matrix.T, pre.T).T)

    @iterate_over_matrix_pairs_scalars_postmultipliers
    def test_lmult_scalar_inv_lmult(matrix, np_matrix, scalar, post):
        npt.assert_allclose(
            (scalar * matrix.inv) @ post, nla.solve(np_matrix / scalar, post))

    @iterate_over_matrix_pairs_scalars_postmultipliers
    def test_inv_lmult_scalar_lmult(matrix, np_matrix, scalar, post):
        npt.assert_allclose(
            (scalar * matrix).inv @ post, nla.solve(scalar * np_matrix, post))

    @iterate_over_matrix_pairs_vectors
    def test_quadratic_form_inv(matrix, np_matrix, vector):
        npt.assert_allclose(
            vector @ matrix.inv @ vector,
            vector @ nla.solve(np_matrix, vector))


class ExplicitShapeInvertibleMatrixTestCase(
        ExplicitShapeSquareMatrixTestCase, InvertibleMatrixTestCase):

    @iterate_over_matrix_pairs
    def test_array_inv(matrix, np_matrix):
        npt.assert_allclose(matrix.inv.array, nla.inv(np_matrix), atol=ATOL)

    @iterate_over_matrix_pairs
    def test_array_inv_inv(matrix, np_matrix):
        npt.assert_allclose(matrix.inv.inv.array, np_matrix, atol=ATOL)

    @iterate_over_matrix_pairs
    def test_log_abs_det_inv(matrix, np_matrix):
        npt.assert_allclose(
            matrix.inv.log_abs_det, -nla.slogdet(np_matrix)[1], atol=ATOL)


class PositiveDefiniteMatrixTestCase(
        SymmetricMatrixTestCase, InvertibleMatrixTestCase):

    @iterate_over_matrix_pairs_vectors
    def test_pos_def(matrix, np_matrix, vector):
        assert vector @ matrix @ vector > 0

    @iterate_over_matrix_pairs_postmultipliers
    def test_lmult_sqrt(matrix, np_matrix, post):
        npt.assert_allclose(
            matrix.sqrt @ (matrix.sqrt.T @ post), np_matrix @ post)

    @iterate_over_matrix_pairs_premultipliers
    def test_rmult_sqrt(matrix, np_matrix, pre):
        npt.assert_allclose(
            (pre @ matrix.sqrt) @ matrix.sqrt.T, pre @ np_matrix)


class ExplicitShapePositiveDefiniteMatrixTestCase(
        PositiveDefiniteMatrixTestCase,
        ExplicitShapeInvertibleMatrixTestCase,
        ExplicitShapeSymmetricMatrixTestCase):

    @iterate_over_matrix_pairs
    def test_sqrt_array(matrix, np_matrix):
        npt.assert_allclose((matrix.sqrt @ matrix.sqrt.T).array, np_matrix)


class DifferentiableMatrixTestCase(MatrixTestCase):

    def __init__(self, matrix_pairs, grad_log_abs_dets,
                 grad_quadratic_form_invs, rng=None):
        super().__init__(matrix_pairs, rng)
        self.grad_log_abs_dets = grad_log_abs_dets
        self.grad_quadratic_form_invs = grad_quadratic_form_invs

    if AUTOGRAD_AVAILABLE:

        def check_grad_log_abs_det(self, matrix, grad_log_abs_det):
            npt.assert_allclose(matrix.grad_log_abs_det, grad_log_abs_det)

        def test_grad_log_abs_det(self):
            for key, (matrix, np_matrix) in self.matrix_pairs.items():
                yield (self.check_grad_log_abs_det, matrix,
                       self.grad_log_abs_dets[key])

        def check_grad_quadratic_form_inv(
                self, matrix, vector, grad_quadratic_form_inv):
            npt.assert_allclose(
                matrix.grad_quadratic_form_inv(vector),
                grad_quadratic_form_inv(vector))

        def test_grad_quadratic_form_inv(self):
            for key, (matrix, np_matrix) in self.matrix_pairs.items():
                for vector in self.vectors[np_matrix.shape[0]]:
                    yield (self.check_grad_quadratic_form_inv, matrix, vector,
                           self.grad_quadratic_form_invs[key])


class TestImplicitIdentityMatrix(
        SymmetricMatrixTestCase, InvertibleMatrixTestCase):

    def __init__(self):
        super().__init__({sz: (
            matrices.IdentityMatrix(None), np.identity(sz)) for sz in SIZES})


class TestIdentityMatrix(ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        super().__init__({sz: (
            matrices.IdentityMatrix(sz), np.identity(sz)) for sz in SIZES})


class TestPositiveScaledIdentityMatrix(
        DifferentiableMatrixTestCase,
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        rng = np.random.RandomState(SEED)
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        for sz in SIZES:
            scalar = abs(rng.normal())
            matrix_pairs[sz] = (
                matrices.PositiveScaledIdentityMatrix(scalar, sz),
                scalar * np.identity(sz))
            if AUTOGRAD_AVAILABLE:
                grad_log_abs_dets[sz] = grad(
                    lambda s: anp.linalg.slogdet(s * anp.eye(sz))[1])(scalar)
                grad_quadratic_form_invs[sz] = partial(
                    grad(lambda s, v: (v / s) @ v), scalar)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestScaledIdentityMatrix(
        DifferentiableMatrixTestCase, ExplicitShapeSymmetricMatrixTestCase,
        ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        rng = np.random.RandomState(SEED)
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        for sz in SIZES:
            scalar = rng.normal()
            matrix_pairs[sz] = (
                matrices.ScaledIdentityMatrix(scalar, sz),
                scalar * np.identity(sz))
            if AUTOGRAD_AVAILABLE:
                grad_log_abs_dets[sz] = grad(
                    lambda s: anp.linalg.slogdet(s * anp.eye(sz))[1])(scalar)
                grad_quadratic_form_invs[sz] = partial(
                    grad(lambda s, v: (v / s) @ v), scalar)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestImplicitScaledIdentityMatrix(
        InvertibleMatrixTestCase, SymmetricMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            scalar = rng.normal()
            matrix_pairs[sz] = (
                matrices.ScaledIdentityMatrix(scalar, None),
                scalar * np.identity(sz))
        super().__init__(matrix_pairs, rng)


class TestPositiveDiagonalMatrix(
        DifferentiableMatrixTestCase,
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        rng = np.random.RandomState(SEED)
        if AUTOGRAD_AVAILABLE:
            grad_log_abs_det_func = grad(
                lambda d: anp.linalg.slogdet(anp.diag(d))[1])
            grad_quadratic_form_inv_func = grad(
                lambda d, v: v @ anp.diag(1 / d) @ v)
        for sz in SIZES:
            diagonal = np.abs(rng.standard_normal(sz))
            matrix_pairs[sz] = (
                matrices.PositiveDiagonalMatrix(diagonal), np.diag(diagonal))
            if AUTOGRAD_AVAILABLE:
                grad_log_abs_dets[sz] = grad_log_abs_det_func(diagonal)
                grad_quadratic_form_invs[sz] = partial(
                    grad_quadratic_form_inv_func, diagonal)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestDiagonalMatrix(
        DifferentiableMatrixTestCase, ExplicitShapeSymmetricMatrixTestCase,
        ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        rng = np.random.RandomState(SEED)
        if AUTOGRAD_AVAILABLE:
            grad_log_abs_det_func = grad(
                lambda d: anp.linalg.slogdet(anp.diag(d))[1])
            grad_quadratic_form_inv_func = grad(
                lambda d, v: v @ anp.diag(1 / d) @ v)
        for sz in SIZES:
            diagonal = rng.standard_normal(sz)
            matrix_pairs[sz] = (
                matrices.DiagonalMatrix(diagonal), np.diag(diagonal))
            if AUTOGRAD_AVAILABLE:
                grad_log_abs_dets[sz] = grad_log_abs_det_func(diagonal)
                grad_quadratic_form_invs[sz] = partial(
                    grad_quadratic_form_inv_func, diagonal)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestTriangularMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            for lower in [True, False]:
                array = rng.standard_normal((sz, sz))
                tri_array = np.tril(array) if lower else np.triu(array)
                matrix_pairs[(sz, lower)] = (
                    matrices.TriangularMatrix(tri_array, lower), tri_array)
        super().__init__(matrix_pairs, rng)


class TestInverseTriangularMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            for lower in [True, False]:
                array = rng.standard_normal((sz, sz))
                inv_tri_array = np.tril(array) if lower else np.triu(array)
                matrix_pairs[(sz, lower)] = (
                    matrices.InverseTriangularMatrix(inv_tri_array, lower),
                    nla.inv(inv_tri_array))
        super().__init__(matrix_pairs, rng)


class TestTriangularFactoredDefiniteMatrix(
        ExplicitShapeSymmetricMatrixTestCase,
        ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            for lower in [True, False]:
                for sign in [+1, -1]:
                    array = rng.standard_normal((sz, sz))
                    chol_array = sla.cholesky(array @ array.T, lower)
                    matrix_pairs[(sz, lower, sign)] = (
                        matrices.TriangularFactoredDefiniteMatrix(
                            chol_array, lower, sign),
                        sign * (chol_array @ chol_array.T))
        super().__init__(matrix_pairs, rng)


class TestTriangularFactoredPositiveDefiniteMatrix(
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            for lower in [True, False]:
                array = rng.standard_normal((sz, sz))
                chol_array = sla.cholesky(array @ array.T, lower)
                matrix_pairs[(sz, lower)] = (
                    matrices.TriangularFactoredPositiveDefiniteMatrix(
                        chol_array, lower),
                    chol_array @ chol_array.T)
        super().__init__(matrix_pairs, rng)


class TestDenseDefiniteMatrix(
        DifferentiableMatrixTestCase, ExplicitShapeSymmetricMatrixTestCase,
        ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        rng = np.random.RandomState(SEED)
        if AUTOGRAD_AVAILABLE:
            grad_log_abs_det_func = grad(lambda a: anp.linalg.slogdet(a)[1])
            grad_quadratic_form_inv_func = grad(
                lambda a, v: v @ anp.linalg.solve(a, v))
        for sz in SIZES:
            for lower in [True, False]:
                for sign in [+1, -1]:
                    sqrt = rng.standard_normal((sz, sz))
                    array = sign * sqrt @ sqrt.T
                    matrix_pairs[(sz, lower, sign)] = (
                        matrices.DenseDefiniteMatrix(array, sign), array)
                    if AUTOGRAD_AVAILABLE:
                        grad_log_abs_dets[(sz, lower, sign)] = (
                            grad_log_abs_det_func(array))
                        grad_quadratic_form_invs[(sz, lower, sign)] = (
                            partial(grad_quadratic_form_inv_func, array))
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestDensePositiveDefiniteMatrix(
        DifferentiableMatrixTestCase,
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        rng = np.random.RandomState(SEED)
        if AUTOGRAD_AVAILABLE:
            grad_log_abs_det_func = grad(lambda a: anp.linalg.slogdet(a)[1])
            grad_quadratic_form_inv_func = grad(
                lambda a, v: v @ anp.linalg.solve(a, v))
        for sz in SIZES:
            sqrt = rng.standard_normal((sz, sz))
            array = sqrt @ sqrt.T
            matrix_pairs[sz] = (
                matrices.DensePositiveDefiniteMatrix(array), array)
            if AUTOGRAD_AVAILABLE:
                grad_log_abs_dets[sz] = grad_log_abs_det_func(array)
                grad_quadratic_form_invs[sz] = partial(
                    grad_quadratic_form_inv_func, array)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestDenseNegativeDefiniteMatrix(
        DifferentiableMatrixTestCase, ExplicitShapeSymmetricMatrixTestCase,
        ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        rng = np.random.RandomState(SEED)
        if AUTOGRAD_AVAILABLE:
            grad_log_abs_det_func = grad(lambda a: anp.linalg.slogdet(a)[1])
            grad_quadratic_form_inv_func = grad(
                lambda a, v: v @ anp.linalg.solve(a, v))
        for sz in SIZES:
            sqrt = rng.standard_normal((sz, sz))
            array = -sqrt @ sqrt.T
            matrix_pairs[sz] = (
                matrices.DenseNegativeDefiniteMatrix(array), array)
            if AUTOGRAD_AVAILABLE:
                grad_log_abs_dets[sz] = grad_log_abs_det_func(array)
                grad_quadratic_form_invs[sz] = partial(
                    grad_quadratic_form_inv_func, array)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestDenseSquareMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            array = rng.standard_normal((sz, sz))
            matrix_pairs[sz] = (
                matrices.DenseSquareMatrix(array), array)
        super().__init__(matrix_pairs, rng)


class TestInverseLUFactoredSquareMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            for transposed in [True, False]:
                inverse_array = rng.standard_normal((sz, sz))
                inverse_lu_and_piv = sla.lu_factor(
                    inverse_array.T if transposed else inverse_array)
                array = nla.inv(inverse_array)
                matrix_pairs[(sz, transposed)] = (
                    matrices.InverseLUFactoredSquareMatrix(
                        inverse_array, inverse_lu_and_piv, transposed), array)
            super().__init__(matrix_pairs, rng)


class TestOrthogonalMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            array = nla.qr(rng.standard_normal((sz, sz)))[0]
            matrix_pairs[sz] = (matrices.OrthogonalMatrix(array), array)
            super().__init__(matrix_pairs, rng)


class TestScaledOrthogonalMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            orth_array = nla.qr(rng.standard_normal((sz, sz)))[0]
            scalar = rng.standard_normal()
            matrix_pairs[sz] = (
                matrices.ScaledOrthogonalMatrix(scalar, orth_array),
                scalar * orth_array)
            super().__init__(matrix_pairs, rng)


class TestEigendecomposedSymmetricMatrix(ExplicitShapeInvertibleMatrixTestCase,
                                         ExplicitShapeSymmetricMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            eigvec = nla.qr(rng.standard_normal((sz, sz)))[0]
            eigval = rng.standard_normal(sz)
            matrix_pairs[sz] = (
                matrices.EigendecomposedSymmetricMatrix(eigvec, eigval),
                (eigvec * eigval) @ eigvec.T)
        super().__init__(matrix_pairs, rng)


class TestEigendecomposedPositiveDefiniteMatrix(
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for sz in SIZES:
            eigvec = nla.qr(rng.standard_normal((sz, sz)))[0]
            eigval = np.abs(rng.standard_normal(sz))
            matrix_pairs[sz] = (
                matrices.EigendecomposedPositiveDefiniteMatrix(eigvec, eigval),
                (eigvec * eigval) @ eigvec.T)
        super().__init__(matrix_pairs, rng)


class TestSoftAbsRegularisedPositiveDefiniteMatrix(
        DifferentiableMatrixTestCase,
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs = {}, {}, {}
        rng = np.random.RandomState(SEED)
        if AUTOGRAD_AVAILABLE:
            def softabs_reg(sym_array, softabs_coeff):
                sym_array = (sym_array + sym_array.T) / 2
                unreg_eigval, eigvec = anp.linalg.eigh(sym_array)
                eigval = unreg_eigval / anp.tanh(unreg_eigval * softabs_coeff)
                return (eigvec * eigval) @ eigvec.T
            grad_log_abs_det_func = grad(
                lambda a, s: anp.linalg.slogdet(softabs_reg(a, s))[1])
            grad_quadratic_form_inv_func = grad(
                lambda a, s, v: v @ anp.linalg.solve(softabs_reg(a, s), v))
        for sz in SIZES:
            for softabs_coeff in [0.5, 1., 1.5]:
                sym_array = rng.standard_normal((sz, sz))
                sym_array += sym_array.T
                unreg_eigval, eigvec = np.linalg.eigh(sym_array)
                eigval = unreg_eigval / np.tanh(unreg_eigval * softabs_coeff)
                matrix_pairs[(sz, softabs_coeff)] = (
                    matrices.SoftAbsRegularisedPositiveDefiniteMatrix(
                        sym_array, softabs_coeff
                    ), (eigvec * eigval) @ eigvec.T)
                if AUTOGRAD_AVAILABLE:
                    grad_log_abs_dets[(sz, softabs_coeff)] = (
                        grad_log_abs_det_func(sym_array, softabs_coeff))
                    grad_quadratic_form_invs[(sz, softabs_coeff)] = partial(
                        grad_quadratic_form_inv_func, sym_array, softabs_coeff)
        super().__init__(
            matrix_pairs, grad_log_abs_dets, grad_quadratic_form_invs, rng)


class TestSquareBlockDiagonalMatrix(ExplicitShapeInvertibleMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for s in SIZES:
            for n_block in [1, 2, 5]:
                arrays = [rng.standard_normal((s, s)) for _ in range(n_block)]
                matrix_pairs[(s, n_block)] = (
                    matrices.SquareBlockDiagonalMatrix(
                        matrices.DenseSquareMatrix(arr) for arr in arrays),
                    sla.block_diag(*arrays))
        super().__init__(matrix_pairs, rng)


class TestSymmetricBlockDiagonalMatrix(
        ExplicitShapeInvertibleMatrixTestCase,
        ExplicitShapeSymmetricMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for s in SIZES:
            for n_block in [1, 2, 5]:
                arrays = [rng.standard_normal((s, s)) for _ in range(n_block)]
                arrays = [arr @ arr.T for arr in arrays]
                matrix_pairs[(s, n_block)] = (
                    matrices.SymmetricBlockDiagonalMatrix(
                        matrices.DensePositiveDefiniteMatrix(arr)
                        for arr in arrays),
                    sla.block_diag(*arrays))
        super().__init__(matrix_pairs, rng)


class TestPositiveDefiniteBlockDiagonalMatrix(
        ExplicitShapePositiveDefiniteMatrixTestCase):

    def __init__(self):
        matrix_pairs = {}
        rng = np.random.RandomState(SEED)
        for s in SIZES:
            for n_block in [1, 2, 5]:
                arrays = [rng.standard_normal((s, s)) for _ in range(n_block)]
                arrays = [arr @ arr.T for arr in arrays]
                matrix_pairs[(s, n_block)] = (
                    matrices.PositiveDefiniteBlockDiagonalMatrix(
                        matrices.DensePositiveDefiniteMatrix(arr)
                        for arr in arrays),
                    sla.block_diag(*arrays))
        super().__init__(matrix_pairs, rng)
